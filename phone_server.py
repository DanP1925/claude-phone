"""
claude-phone: an MCP server that lets Claude look at and use an Android phone.

Claude only sees the "menu" (tool names, descriptions and inputs).
The "kitchen" is the adb commands below.
"""

import io
import os
import re
import subprocess
import xml.etree.ElementTree as ET

from mcp.server.mcpserver import Image, MCPServer
from PIL import Image as PILImage

# Full path to adb. Claude Desktop starts with a minimal PATH, so set ADB_PATH
# in the Claude Desktop config if "adb" alone is not found.
ADB = os.environ.get("ADB_PATH", "adb")
# Optional: which device to use when several are connected (see `adb devices`).
SERIAL = os.environ.get("ANDROID_SERIAL")

mcp = MCPServer("phone")


def adb(*args: str) -> bytes:
    cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + list(args)
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip() or "adb failed")
    return result.stdout


def parse_elements(xml_text: str) -> list[str]:
    """Turn a uiautomator XML dump into readable lines with tap coordinates."""
    root = ET.fromstring(xml_text)
    lines = []
    for node in root.iter("node"):
        label = node.get("text") or node.get("content-desc")
        if not label:
            continue
        match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
        if not match:
            continue
        x1, y1, x2, y2 = map(int, match.groups())
        x, y = (x1 + x2) // 2, (y1 + y2) // 2
        details = []
        if node.get("checkable") == "true":
            details.append("ON" if node.get("checked") == "true" else "OFF")
        if node.get("clickable") == "true":
            details.append("clickable")
        extra = f" [{', '.join(details)}]" if details else ""
        lines.append(f'"{label}" at ({x}, {y}){extra}')
    return lines


@mcp.tool()
def screenshot() -> Image:
    """Take a screenshot to see what is on the phone screen right now.
    Use it to understand the screen. To tap something, prefer the coordinates
    from list_elements, because this image is scaled down."""
    png = adb("exec-out", "screencap", "-p")
    img = PILImage.open(io.BytesIO(png)).convert("RGB")
    img.thumbnail((720, 720))  # smaller image = faster for Claude
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    return Image(data=buffer.getvalue(), format="jpeg")


@mcp.tool()
def list_elements() -> str:
    """List the text and buttons on the current screen with exact tap coordinates.
    Use this before tapping, then call tap with the coordinates shown."""
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    xml_text = adb("exec-out", "cat", "/sdcard/ui.xml").decode(errors="replace")
    lines = parse_elements(xml_text)
    return "\n".join(lines) if lines else "No text found on screen. Try screenshot."


@mcp.tool()
def tap(x: int, y: int) -> str:
    """Tap the screen at pixel coordinates (x, y), like pressing with a finger."""
    adb("shell", "input", "tap", str(x), str(y))
    return f"Tapped ({x}, {y})"


@mcp.tool()
def type_text(text: str) -> str:
    """Type text into the field that is currently selected."""
    adb("shell", "input", "text", text.replace(" ", "%s"))
    return f"Typed: {text}"


@mcp.tool()
def scroll(direction: str = "down") -> str:
    """Scroll the screen. direction is "down" or "up"."""
    size = adb("shell", "wm", "size").decode()
    width, height = map(int, re.findall(r"(\d+)x(\d+)", size)[-1])
    x = width // 2
    start, end = (height * 3 // 4, height // 4) if direction == "down" else (height // 4, height * 3 // 4)
    adb("shell", "input", "swipe", str(x), str(start), str(x), str(end), "300")
    return f"Scrolled {direction}"


@mcp.tool()
def press_button(button: str) -> str:
    """Press a phone button: "back" or "home"."""
    codes = {"back": "KEYCODE_BACK", "home": "KEYCODE_HOME"}
    if button not in codes:
        return 'Unknown button. Use "back" or "home".'
    adb("shell", "input", "keyevent", codes[button])
    return f"Pressed {button}"


@mcp.tool()
def open_app(package: str) -> str:
    """Open an installed app by its package name.
    Example: the Settings app is com.android.settings"""
    adb("shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1")
    return f"Opened {package}"


if __name__ == "__main__":
    mcp.run()
