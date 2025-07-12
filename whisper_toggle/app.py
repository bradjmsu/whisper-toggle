"""
Main application class for Whisper Toggle.

Integrates all components including GUI, tray icon, and transcription.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import threading
import logging
import sys
from typing import Optional

from .config import Config
from .gui import SettingsWindow
from .tray import TrayIcon
from .main import ToggleTranscriber  # Import the main transcription logic

logger = logging.getLogger(__name__)


class WhisperToggleApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        # Load configuration
        self.config = Config()
        
        # Create tray icon
        self.tray = TrayIcon(
            on_toggle_callback=self.toggle_recording,
            on_settings_callback=self.show_settings,
            on_quit_callback=self.quit_app
        )
        
        # Settings window (created on demand)
        self.settings_window: Optional[SettingsWindow] = None
        
        # Initialize transcription engine
        self.whisper_toggle: Optional[ToggleTranscriber] = None
        self.init_transcription_engine()
        
        # Recording state
        self.is_recording = False
        
        # Show settings on first run or if not minimized
        if not self.config.start_minimized:
            GLib.idle_add(self.show_settings)
    
    def init_transcription_engine(self):
        """Initialize the transcription engine with current settings."""
        try:
            # Stop existing engine if running
            if self.whisper_toggle:
                self.whisper_toggle.stop()
            
            # Create new engine with config
            device_index = self.config.audio_device if self.config.audio_device is not None else 3
            self.whisper_toggle = ToggleTranscriber(
                silence_threshold=int(self.config.silence_threshold * 10),  # Convert to counter units
                model_size=self.config.whisper_model,
                device_index=device_index
            )
            
            # Start keyboard listener in background thread
            self.whisper_thread = threading.Thread(
                target=self.whisper_toggle.run,
                daemon=True
            )
            self.whisper_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to initialize transcription engine: {e}")
            self.show_error(
                "Initialization Error",
                f"Failed to initialize transcription engine:\n{str(e)}"
            )
    
    def on_recording_status_changed(self, is_recording: bool):
        """Handle recording status change from transcription engine."""
        GLib.idle_add(self._update_recording_status, is_recording)
    
    def _update_recording_status(self, is_recording: bool):
        """Update UI based on recording status (runs in GTK thread)."""
        self.is_recording = is_recording
        self.tray.update_icon(is_recording)
        
        if is_recording:
            self.tray.set_status("Recording...")
            if self.config.show_notifications:
                self.tray.show_notification(
                    "Whisper Toggle",
                    "Recording started",
                    "audio-input-microphone-high"
                )
        else:
            self.tray.set_status("Ready")
            if self.config.show_notifications:
                self.tray.show_notification(
                    "Whisper Toggle",
                    "Recording stopped",
                    "audio-input-microphone"
                )
    
    def toggle_recording(self):
        """Toggle recording on/off."""
        if self.whisper_toggle:
            self.whisper_toggle.toggle_recording()
    
    def show_settings(self):
        """Show the settings window."""
        if self.settings_window is None or not self.settings_window.get_visible():
            self.settings_window = SettingsWindow(
                self.config,
                on_save_callback=self.on_settings_saved
            )
            self.settings_window.connect("destroy", self.on_settings_closed)
        else:
            self.settings_window.present()
    
    def on_settings_closed(self, window):
        """Handle settings window closed."""
        self.settings_window = None
    
    def on_settings_saved(self, config):
        """Handle settings saved."""
        # Reinitialize transcription engine with new settings
        self.init_transcription_engine()
        
        # Handle auto-start setting
        if config.auto_start:
            self.enable_autostart()
        else:
            self.disable_autostart()
    
    def enable_autostart(self):
        """Enable application autostart."""
        # TODO: Implement autostart desktop file creation
        pass
    
    def disable_autostart(self):
        """Disable application autostart."""
        # TODO: Implement autostart desktop file removal
        pass
    
    def show_error(self, title: str, message: str):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def quit_app(self):
        """Quit the application."""
        # Stop transcription engine
        if self.whisper_toggle:
            self.whisper_toggle.stop()
        
        # Save config
        self.config.save()
        
        # Quit GTK
        Gtk.main_quit()
    
    def run(self):
        """Run the application."""
        try:
            Gtk.main()
        except KeyboardInterrupt:
            self.quit_app()


def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check for required dependencies
    try:
        import pyaudio
        import evdev
        from faster_whisper import WhisperModel
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install all dependencies with: pip install -e .")
        sys.exit(1)
    
    # Create and run application
    app = WhisperToggleApp()
    app.run()


if __name__ == "__main__":
    main()