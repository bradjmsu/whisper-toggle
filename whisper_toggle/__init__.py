"""
Whisper Toggle - Real-time voice transcription with hardware toggle

A privacy-focused voice transcription tool that runs locally and provides
real-time speech-to-text conversion with hardware button toggle support.
"""

__version__ = "1.0.0"
__author__ = "Brad Johnson"
__email__ = "brad@bradjohnson.ai"

from .config import Config
from .tray import TrayIcon
from .gui import SettingsWindow
from .app import WhisperToggleApp, main

__all__ = ['Config', 'TrayIcon', 'SettingsWindow', 'WhisperToggleApp', 'main']