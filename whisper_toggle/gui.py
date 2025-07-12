"""
GTK-based GUI for Whisper Toggle settings.

Provides a settings window for configuring the application.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import List, Optional, Tuple
import logging

from .config import Config
from .audio_test import AudioTestDialog, get_audio_devices

logger = logging.getLogger(__name__)


class SettingsWindow(Gtk.Window):
    """Settings window for Whisper Toggle."""
    
    def __init__(self, config: Config, on_save_callback=None):
        super().__init__(title="Whisper Toggle Settings")
        self.config = config
        self.on_save_callback = on_save_callback
        
        self.set_default_size(600, 500)
        self.set_border_width(10)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Create main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Create notebook for tabs
        notebook = Gtk.Notebook()
        vbox.pack_start(notebook, True, True, 0)
        
        # Add tabs
        notebook.append_page(self.create_general_tab(), Gtk.Label(label="General"))
        notebook.append_page(self.create_audio_tab(), Gtk.Label(label="Audio"))
        notebook.append_page(self.create_hotkey_tab(), Gtk.Label(label="Hotkey"))
        notebook.append_page(self.create_advanced_tab(), Gtk.Label(label="Advanced"))
        
        # Create button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        vbox.pack_start(button_box, False, False, 0)
        
        # Add buttons
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self.on_cancel_clicked)
        button_box.pack_start(cancel_button, False, False, 0)
        
        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", self.on_apply_clicked)
        button_box.pack_start(apply_button, False, False, 0)
        
        save_button = Gtk.Button(label="Save")
        save_button.get_style_context().add_class("suggested-action")
        save_button.connect("clicked", self.on_save_clicked)
        button_box.pack_start(save_button, False, False, 0)
        
        self.show_all()
    
    def create_general_tab(self) -> Gtk.Widget:
        """Create general settings tab."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        
        # Whisper model selection
        model_frame = Gtk.Frame(label="Whisper Model")
        vbox.pack_start(model_frame, False, False, 0)
        
        model_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        model_box.set_border_width(10)
        model_frame.add(model_box)
        
        self.model_combo = Gtk.ComboBoxText()
        models = [
            ("tiny", "Tiny (39M) - Fastest, least accurate"),
            ("base", "Base (74M) - Good balance"),
            ("small", "Small (244M) - Better accuracy"),
            ("medium", "Medium (769M) - Even better accuracy"),
            ("large", "Large (1550M) - Best accuracy, slowest")
        ]
        
        for model_id, description in models:
            self.model_combo.append(model_id, description)
        
        self.model_combo.set_active_id(self.config.whisper_model)
        model_box.pack_start(self.model_combo, False, False, 0)
        
        # Language selection
        lang_frame = Gtk.Frame(label="Transcription Language")
        vbox.pack_start(lang_frame, False, False, 0)
        
        lang_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        lang_box.set_border_width(10)
        lang_frame.add(lang_box)
        
        self.language_combo = Gtk.ComboBoxText()
        languages = [
            ("en", "English"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("de", "German"),
            ("it", "Italian"),
            ("pt", "Portuguese"),
            ("ru", "Russian"),
            ("ja", "Japanese"),
            ("ko", "Korean"),
            ("zh", "Chinese"),
        ]
        
        for lang_code, lang_name in languages:
            self.language_combo.append(lang_code, lang_name)
        
        self.language_combo.set_active_id(self.config.language)
        lang_box.pack_start(self.language_combo, False, False, 0)
        
        # UI options
        ui_frame = Gtk.Frame(label="User Interface")
        vbox.pack_start(ui_frame, False, False, 0)
        
        ui_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        ui_box.set_border_width(10)
        ui_frame.add(ui_box)
        
        self.start_minimized_check = Gtk.CheckButton(label="Start minimized to tray")
        self.start_minimized_check.set_active(self.config.start_minimized)
        ui_box.pack_start(self.start_minimized_check, False, False, 0)
        
        self.show_notifications_check = Gtk.CheckButton(label="Show notifications")
        self.show_notifications_check.set_active(self.config.show_notifications)
        ui_box.pack_start(self.show_notifications_check, False, False, 0)
        
        self.play_sounds_check = Gtk.CheckButton(label="Play sound effects")
        self.play_sounds_check.set_active(self.config.play_sounds)
        ui_box.pack_start(self.play_sounds_check, False, False, 0)
        
        self.auto_start_check = Gtk.CheckButton(label="Start on system boot")
        self.auto_start_check.set_active(self.config.auto_start)
        ui_box.pack_start(self.auto_start_check, False, False, 0)
        
        return vbox
    
    def create_audio_tab(self) -> Gtk.Widget:
        """Create audio settings tab."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        
        # Microphone selection
        mic_frame = Gtk.Frame(label="Microphone")
        vbox.pack_start(mic_frame, False, False, 0)
        
        mic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        mic_box.set_border_width(10)
        mic_frame.add(mic_box)
        
        self.mic_combo = Gtk.ComboBoxText()
        self.mic_combo.append("-1", "Auto-detect")
        
        # Get available audio devices
        devices = get_audio_devices()
        for dev in devices:
            device_name = f"{dev['name']} ({dev['host_api']})"
            self.mic_combo.append(str(dev['index']), device_name)
        
        current_device = str(self.config.audio_device) if self.config.audio_device is not None else "-1"
        self.mic_combo.set_active_id(current_device)
        mic_box.pack_start(self.mic_combo, False, False, 0)
        
        # Test microphone button
        test_button = Gtk.Button(label="Test Microphone")
        test_button.connect("clicked", self.on_test_microphone)
        mic_box.pack_start(test_button, False, False, 0)
        
        # Audio thresholds
        threshold_frame = Gtk.Frame(label="Audio Processing")
        vbox.pack_start(threshold_frame, False, False, 0)
        
        threshold_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        threshold_box.set_border_width(10)
        threshold_frame.add(threshold_box)
        
        # Silence threshold
        silence_label = Gtk.Label(label="Silence threshold (seconds):", xalign=0)
        threshold_box.pack_start(silence_label, False, False, 0)
        
        self.silence_adjustment = Gtk.Adjustment(
            value=self.config.silence_threshold,
            lower=0.1,
            upper=3.0,
            step_increment=0.1,
            page_increment=0.5
        )
        self.silence_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=self.silence_adjustment
        )
        self.silence_scale.set_digits(2)
        self.silence_scale.add_mark(0.5, Gtk.PositionType.BOTTOM, "Fast")
        self.silence_scale.add_mark(1.5, Gtk.PositionType.BOTTOM, "Balanced")
        self.silence_scale.add_mark(2.5, Gtk.PositionType.BOTTOM, "Accurate")
        threshold_box.pack_start(self.silence_scale, False, False, 0)
        
        # Audio level threshold
        level_label = Gtk.Label(label="Audio level threshold:", xalign=0)
        threshold_box.pack_start(level_label, False, False, 0)
        
        self.level_adjustment = Gtk.Adjustment(
            value=self.config.audio_threshold,
            lower=0.001,
            upper=0.1,
            step_increment=0.001,
            page_increment=0.01
        )
        self.level_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=self.level_adjustment
        )
        self.level_scale.set_digits(3)
        self.level_scale.add_mark(0.01, Gtk.PositionType.BOTTOM, "Sensitive")
        self.level_scale.add_mark(0.05, Gtk.PositionType.BOTTOM, "Normal")
        self.level_scale.add_mark(0.09, Gtk.PositionType.BOTTOM, "Loud")
        threshold_box.pack_start(self.level_scale, False, False, 0)
        
        return vbox
    
    def create_hotkey_tab(self) -> Gtk.Widget:
        """Create hotkey settings tab."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        
        # Hotkey selection
        hotkey_frame = Gtk.Frame(label="Toggle Hotkey")
        vbox.pack_start(hotkey_frame, False, False, 0)
        
        hotkey_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hotkey_box.set_border_width(10)
        hotkey_frame.add(hotkey_box)
        
        # Current hotkey display
        current_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hotkey_box.pack_start(current_box, False, False, 0)
        
        current_label = Gtk.Label(label="Current hotkey:")
        current_box.pack_start(current_label, False, False, 0)
        
        self.hotkey_label = Gtk.Label()
        self.hotkey_label.set_markup(f"<b>{self.config.toggle_key}</b>")
        current_box.pack_start(self.hotkey_label, False, False, 0)
        
        # Hotkey selection button
        self.hotkey_button = Gtk.Button(label="Press to set new hotkey...")
        self.hotkey_button.connect("clicked", self.on_set_hotkey)
        hotkey_box.pack_start(self.hotkey_button, False, False, 0)
        
        # Common hotkeys
        common_label = Gtk.Label(label="Or choose a common hotkey:", xalign=0)
        hotkey_box.pack_start(common_label, False, False, 0)
        
        common_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        hotkey_box.pack_start(common_box, False, False, 0)
        
        common_keys = [
            ("KEY_F16", "F16 (Keychron X button)"),
            ("KEY_F13", "F13"),
            ("KEY_F14", "F14"),
            ("KEY_F15", "F15"),
            ("KEY_SCROLLLOCK", "Scroll Lock"),
            ("KEY_PAUSE", "Pause/Break"),
        ]
        
        for key_code, key_name in common_keys:
            button = Gtk.Button(label=key_name)
            button.connect("clicked", self.on_common_key_clicked, key_code)
            common_box.pack_start(button, False, False, 0)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<small>Note: Choose a key that you don't normally use.\n"
            "Some keys may not work depending on your keyboard and system.</small>"
        )
        instructions.set_line_wrap(True)
        instructions.set_xalign(0)
        vbox.pack_end(instructions, False, False, 0)
        
        return vbox
    
    def create_advanced_tab(self) -> Gtk.Widget:
        """Create advanced settings tab."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        
        # About section
        about_frame = Gtk.Frame(label="About")
        vbox.pack_start(about_frame, False, False, 0)
        
        about_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        about_box.set_border_width(10)
        about_frame.add(about_box)
        
        about_label = Gtk.Label()
        about_label.set_markup(
            "<b>Whisper Toggle</b>\n"
            "Version 1.0.0\n\n"
            "Real-time voice transcription with hardware toggle\n"
            "Using OpenAI Whisper for speech recognition\n\n"
            "© 2025 Brad Johnson"
        )
        about_label.set_xalign(0)
        about_box.pack_start(about_label, False, False, 0)
        
        # Reset settings
        reset_frame = Gtk.Frame(label="Reset")
        vbox.pack_end(reset_frame, False, False, 0)
        
        reset_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        reset_box.set_border_width(10)
        reset_frame.add(reset_box)
        
        reset_button = Gtk.Button(label="Reset All Settings to Defaults")
        reset_button.get_style_context().add_class("destructive-action")
        reset_button.connect("clicked", self.on_reset_clicked)
        reset_box.pack_start(reset_button, False, False, 0)
        
        return vbox
    
    def on_test_microphone(self, button):
        """Test the selected microphone."""
        device_id = self.mic_combo.get_active_id()
        if device_id == "-1":
            device_index = None
        else:
            device_index = int(device_id)
        
        # Open audio test dialog
        dialog = AudioTestDialog(self, device_index)
        dialog.run()
    
    def on_set_hotkey(self, button):
        """Set a new hotkey."""
        # TODO: Implement hotkey capture dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Set Hotkey"
        )
        dialog.format_secondary_text(
            "Press any key to set as hotkey...\n"
            "This feature will be implemented soon."
        )
        dialog.run()
        dialog.destroy()
    
    def on_common_key_clicked(self, button, key_code):
        """Set a common hotkey."""
        self.hotkey_label.set_markup(f"<b>{key_code}</b>")
    
    def on_reset_clicked(self, button):
        """Reset all settings to defaults."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Reset All Settings?"
        )
        dialog.format_secondary_text(
            "This will reset all settings to their default values.\n"
            "This action cannot be undone."
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.config.reset()
            self.load_settings()
    
    def load_settings(self):
        """Load settings from config into UI."""
        self.model_combo.set_active_id(self.config.whisper_model)
        self.language_combo.set_active_id(self.config.language)
        self.start_minimized_check.set_active(self.config.start_minimized)
        self.show_notifications_check.set_active(self.config.show_notifications)
        self.play_sounds_check.set_active(self.config.play_sounds)
        self.auto_start_check.set_active(self.config.auto_start)
        
        device_id = str(self.config.audio_device) if self.config.audio_device is not None else "-1"
        self.mic_combo.set_active_id(device_id)
        
        self.silence_adjustment.set_value(self.config.silence_threshold)
        self.level_adjustment.set_value(self.config.audio_threshold)
        
        self.hotkey_label.set_markup(f"<b>{self.config.toggle_key}</b>")
    
    def save_settings(self):
        """Save UI settings to config."""
        self.config.set('whisper_model', self.model_combo.get_active_id())
        self.config.set('language', self.language_combo.get_active_id())
        self.config.set('start_minimized', self.start_minimized_check.get_active())
        self.config.set('show_notifications', self.show_notifications_check.get_active())
        self.config.set('play_sounds', self.play_sounds_check.get_active())
        self.config.set('auto_start', self.auto_start_check.get_active())
        
        device_id = self.mic_combo.get_active_id()
        if device_id == "-1":
            self.config.set('audio_device', None)
        else:
            self.config.set('audio_device', int(device_id))
        
        self.config.set('silence_threshold', self.silence_adjustment.get_value())
        self.config.set('audio_threshold', self.level_adjustment.get_value())
        
        # Get hotkey from label
        hotkey = self.hotkey_label.get_text()
        if hotkey:
            self.config.set('toggle_key', hotkey)
    
    def on_cancel_clicked(self, button):
        """Handle cancel button click."""
        self.close()
    
    def on_apply_clicked(self, button):
        """Handle apply button click."""
        self.save_settings()
        if self.on_save_callback:
            self.on_save_callback(self.config)
    
    def on_save_clicked(self, button):
        """Handle save button click."""
        self.save_settings()
        self.config.save()
        if self.on_save_callback:
            self.on_save_callback(self.config)
        self.close()