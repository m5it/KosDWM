# KosDWM Agent Guide

## Key Commands
- Run: `python run.py`
- Config: Edit `~/.config/KosDWM/config.json`
- Test: Check `test/` directory (if tests exist)

## Important Files
- Entry point: `run.py`
- Config manager: `src/config.py`
- Helper functions: `src/functions.py`
- Default config location: `~/.config/KosDWM/config.json`

## Layout Modes
Set in config:
- `"layout_mode": "buttons"` - Desktop buttons + all windows combobox
- `"layout_mode": "comboboxes"` - 4 desktop window comboboxes only

## External Dependencies
- Requires `wmctrl` command for window management
- Requires `screeninfo` Python package
- Uses standard Tkinter

## Recent Changes
- Added red frame (2px height) under the four comboboxes/buttons in both layout modes (visible in run.py)
- Added application menu (Help -> About) that appears on root window hover and shows content from ABOUT.md (visible in run.py)
- Removed legacy help/menu button functionality
- Removed xterm script logging feature (reptyr cannot attach to existing processes)

## Common Gotchas
- Menu functionality is commented out in `create_widgets()` (lines 411-418) - uncomment to enable
- Window positioning in `on_menu_enter()` uses root window coordinates; may need adjustment when dragged
- Config file is created at first run in `~/.config/KosDWM/`
- Threading used for observer and time update loops

## Verification
- Check `wmctrl -l` output format matches parsing expectations
- Verify `screeninfo.get_monitors()[0]` returns expected primary monitor
- Test config loading/saving through Config class
- Verify red frame appears under comboboxes in both layout modes