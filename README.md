# claude-phone

Give Claude hands on an Android phone. Ask it to *"turn on dark mode"* and watch it look at the screen, open Settings and flip the switch, all by itself.

This is a tiny **MCP server**: about 100 lines of Python that you can read in five minutes.

## The idea in one picture

Claude never runs your code directly. It only sees a **menu**: the name, description and inputs of each tool. When it orders something, your server cooks it and brings the result back.

| Claude's menu (what it sees) | The kitchen (what actually runs) |
|---|---|
| `screenshot()`: see the screen | `adb exec-out screencap -p` |
| `list_elements()`: read text and buttons | `adb shell uiautomator dump` |
| `tap(x, y)`: press somewhere | `adb shell input tap x y` |
| `type_text(text)`: write something | `adb shell input text …` |
| `scroll(direction)`: scroll up or down | `adb shell input swipe …` |
| `press_button(button)`: back or home | `adb shell input keyevent …` |
| `open_app(package)`: open an app | `adb shell monkey -p …` |

Claude then repeats **look → decide → act → look again** until the task is done. That loop is what people mean by an "AI agent."

Want to build your own server? Copy this file, delete the phone tools, and write any Python function with a clear docstring. Same shape, any idea.

## What you need

- [Claude Desktop](https://claude.ai/download)
- An Android phone or emulator. The easiest option is to create an emulator in [Android Studio](https://developer.android.com/studio) → Device Manager.
- `adb`, which comes with Android Studio (in `platform-tools`). Check it works: `adb devices` should list your device.
- [uv](https://docs.astral.sh/uv/getting-started/installation/), a Python runner that installs the dependencies for you.

## Setup (5 minutes)

1. Download `phone_server.py` from this repo and note its full path, e.g. `/Users/you/claude-phone/phone_server.py`.
2. Find the full paths of `uv` and `adb`:
   ```bash
   which uv
   which adb   # macOS default: ~/Library/Android/sdk/platform-tools/adb
   ```
3. In Claude Desktop, open **Settings → Developer → Edit Config** and add the following, using your own paths:
   ```json
   {
     "mcpServers": {
       "phone": {
         "command": "/full/path/to/uv",
         "args": ["run", "--with", "mcp>=2", "--with", "pillow", "/full/path/to/phone_server.py"],
         "env": { "ADB_PATH": "/full/path/to/adb" }
       }
     }
   }
   ```
4. Quit and reopen Claude Desktop. The phone tools should now appear in the tools menu.
5. With your emulator running, ask Claude:
   > Turn on dark mode on my phone.

## Troubleshooting

- **The server doesn't show up:** make sure every path in the config is a full path, since Claude Desktop doesn't see your terminal's `PATH`. Check the logs in Settings → Developer.
- **"adb failed" or "no devices":** run `adb devices`. If several devices are listed, add `"ANDROID_SERIAL": "emulator-5554"` (your device's id) to `env`.
- **Taps land in the wrong place:** the screenshot Claude sees is scaled down. The tool descriptions already tell Claude to use `list_elements` coordinates, but you can also say it in your prompt.
- **Test without Claude:** run `uv run --with "mcp[cli]>=2" --with pillow mcp dev phone_server.py` to open the MCP Inspector and call each tool by hand.

## Safety

This server can tap anything on the connected device. Use an emulator or a test phone, and keep Claude Desktop's tool-approval prompts on.
