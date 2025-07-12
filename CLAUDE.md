# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Whisper Toggle is a real-time voice transcription application that uses OpenAI's Whisper model locally. It provides hardware toggle button support (F16 key) for privacy-focused speech-to-text conversion on Linux systems with GNOME/Wayland.

**Key Features:**
- Local processing only (no external API calls)
- Hardware toggle with F16 key (Keychron X button)
- System tray integration with AppIndicator3
- Real-time audio visualization with VU meter
- Multi-language support
- No sudo required (user must be in 'input' group)

## Key Architecture

The application follows a modular architecture:
- **Core Transcription Engine** (`whisper_toggle/main.py`): Handles audio capture, Whisper model inference, and keyboard monitoring
- **Application Controller** (`whisper_toggle/app.py`): Orchestrates GUI, tray icon, and transcription components
- **System Integration**: Uses evdev for keyboard input, ydotool for text output, and PyGObject/GTK for UI
- **Configuration**: YAML-based config management with settings for audio devices, model selection, and user preferences

## Development Commands

### Setup
```bash
# Create virtual environment with system packages (required for PyGObject)
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Install in development mode
pip install -e .[dev]
```

### Testing
```bash
# Run all tests with coverage
pytest tests/ -v --cov=whisper_toggle --cov-report=xml

# Run specific test
pytest tests/test_specific.py::test_function
```

### Code Quality
```bash
# Format code
black whisper_toggle --line-length 88

# Lint code
flake8 whisper_toggle --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

# Type checking
mypy whisper_toggle
```

### Running the Application
```bash
# Run GUI version (recommended)
./run-gui.sh

# Run standalone demo
python whisper-toggle.py

# Test audio devices
python audio_test_standalone.py

# One-click installer (sets up everything)
./install.sh
```

## Important Implementation Notes

1. **Audio Processing**: The application uses PyAudio with NumPy/SciPy for real-time audio processing. Silence detection is critical for performance.

2. **Keyboard Monitoring**: Requires user to be in 'input' group. Uses evdev to monitor /dev/input/ devices for F16 key events.

3. **Wayland Compatibility**: Uses ydotool instead of xdotool for keyboard simulation. Requires ydotool to be properly installed and configured.

4. **GTK Integration**: Requires PyGObject and GTK 3.0. The application uses AppIndicator3 for system tray support.

5. **Model Loading**: Uses faster-whisper for optimized inference. Models are cached locally after first download.

## Testing Approach

- Unit tests focus on configuration and utility functions
- Audio functionality requires manual testing due to hardware dependencies
- Use `test_audio.py` and `demo_*.py` scripts for manual verification
- CI runs on multiple Python versions (3.8-3.11) with mocked audio devices

### CI/CD Pipeline
- GitHub Actions workflow tests on Python 3.8-3.11
- Installs system dependencies (portaudio)
- Runs linting, type checking, and tests
- Tests are currently non-blocking (allowed to fail)

## Common Development Tasks

### Adding a New Feature
1. Update configuration schema if needed (`whisper_toggle/config.py`)
2. Implement feature in appropriate module
3. Add GUI controls if applicable (`whisper_toggle/gui.py`)
4. Update tests
5. Run full test suite and linting

### Debugging Audio Issues
1. Run `python audio_test_standalone.py` to verify device access
2. Check `~/.local/share/whisper-toggle/whisper-toggle.log` for errors
3. Verify user is in 'input' group: `groups $USER`
4. Test with different audio devices using the GUI settings

### Working with the Whisper Model
- Models are stored in `~/.cache/huggingface/`
- Default model is "base" but can be changed in settings
- Larger models provide better accuracy but require more resources
- The application buffers audio to handle processing delays

## Dependencies to Note

- **faster-whisper**: Core transcription engine (not the standard whisper package)
- **evdev**: Linux-specific keyboard monitoring
- **PyGObject**: GTK bindings (requires system packages)
- **ydotool**: Wayland keyboard simulation (must be installed separately)

## Configuration Files

- User settings: `~/.config/whisper-toggle/config.json` (migrated from YAML)
- Logs: `~/.local/share/whisper-toggle/whisper-toggle.log`
- Whisper models: `~/.cache/huggingface/`

## Entry Points

- `whisper_toggle_gui.py` - Main GUI application (what run-gui.sh launches)
- `transcriber_simple.py` - Core transcription engine
- `demo_standalone.py` - Settings window demo
- `audio_test_standalone.py` - Audio device testing with VU meter

Remember: All processing happens locally for privacy. The application never sends audio data to external services.