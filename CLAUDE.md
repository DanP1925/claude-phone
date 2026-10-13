# claude-phone

MCP server (Python, `mcp` SDK v2) that lets Claude control an Android emulator through `adb`. Built as the live demo for a 4-minute talk at the Claude Code BCN meetup, aimed at newbies.

## The demo

- Runs in **Claude Desktop** (not Claude Code), so Claude can't bypass the tools with a terminal command like `adb shell cmd uimode night yes`.
- Prompt on stage: "Turn on dark mode on my phone."
- The emulator starts in light mode on the home screen. Expected path: open Settings → list elements → tap Display → list elements → tap Dark theme.
- Goal: Claude visibly loops look → decide → act. The screen flipping to dark is the payoff moment.

## Code notes

- SDK v2 API: `from mcp.server.mcpserver import MCPServer, Image` (`FastMCP` was renamed in v2).
- `ADB_PATH` and `ANDROID_SERIAL` env vars, because Claude Desktop starts with a minimal PATH.
- `list_elements` uses `uiautomator dump`, so taps use exact coordinates. Screenshots are downscaled and not reliable for coordinates.

## Next steps

1. Test each tool against the real emulator with `mcp dev phone_server.py` (MCP Inspector).
2. Run the dark mode prompt in Claude Desktop several times and note which tools Claude actually uses.
3. Trim the tool list for the demo, probably to `open_app`, `list_elements`, `tap` and maybe `screenshot`. Fewer tools means more predictable behavior and a simpler slide.
4. Measure how long the full run takes, and record a backup video.
