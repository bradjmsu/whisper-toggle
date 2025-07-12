# Changelog

All notable changes to Whisper Toggle will be documented in this file.

## [1.0.0] - 2025-06-18

### Added
- Initial release of Whisper Toggle
- Hardware toggle support for Keychron keyboards (X button / F16 key)
- Real-time speech transcription using OpenAI Whisper
- Smart indicator system with multiple feedback methods:
  - Persistent GNOME notifications with activity display
  - Audio feedback (positive/negative beeps)
  - Desktop status file as backup indicator
- Automatic text typing via ydotool (Wayland compatible)
- System service integration with systemd
- Fast 750ms transcription response time
- Privacy-first design (all processing local)
- Support for multiple audio input devices
- Configurable silence threshold and model size
- Comprehensive installation and setup scripts
- Service management tools
- Audio device compatibility testing
- GNOME/Wayland optimized experience

### Technical Details
- Built on faster-whisper for optimized inference
- Multi-threaded architecture for responsive UI
- Automatic audio resampling for device compatibility
- Robust error handling and service recovery
- Clean shutdown and resource management

### Documentation
- Complete README with installation instructions
- Troubleshooting guide
- Development setup documentation
- Audio device testing utilities
- Service control scripts