# Whisper Toggle

Real-time voice transcription with hardware toggle button.

## Quick Start

To run Whisper Toggle:
```bash
./run-gui.sh
```

The app will appear in your system tray. Press F16 (Keychron X button) to start/stop recording.

## Main Files

- **whisper_toggle_gui.py** - Main application (this is what run-gui.sh launches)
- **transcriber_simple.py** - Core transcription engine
- **config.py** - Configuration management
- **demo_standalone.py** - Settings window GUI
- **audio_test_standalone.py** - Audio testing and gain adjustment

## Features

- Real-time transcription using OpenAI Whisper
- Hardware toggle with F16 key
- System tray integration
- Professional VU meter for audio testing
- Multi-language support
- No sudo required

## Configuration

Settings are stored in `~/.config/whisper-toggle/config.json`

Access settings by right-clicking the system tray icon.

## Troubleshooting

If F16 key doesn't work:
1. Check you're in the `input` group: `groups $USER | grep input`
2. Look for "Found Keychron keyboard" in the console output
3. Use the system tray menu to start/stop recording manually