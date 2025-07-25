#!/usr/bin/env python3
"""
Standalone demo with beautiful GTK interface - no dependencies needed!
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import json
import math
from pathlib import Path

# Minimal config class
class DemoConfig:
    def __init__(self):
        self.config = {
            'toggle_key': 'KEY_F16',
            'audio_device': 1,  # Fifine
            'audio_gain': 1.0,  # Audio gain multiplier
            'whisper_model': 'base',
            'silence_threshold': 0.75,
            'audio_threshold': 0.01,
            'start_minimized': True,
            'show_notifications': True,
            'play_sounds': True,
            'auto_start': False,
            'language': 'en',
            'continuous_mode': False,
            'output_method': 'type',
            # GPU/Performance settings
            'device': 'auto',  # auto, cpu, cuda
            'compute_type': 'auto',  # auto, int8, float16, float32
            'gpu_memory_limit': 0,  # 0 = no limit, >0 = GB limit
        }
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
    
    def save(self):
        print("Settings saved (demo mode)")
        return True
    
    # Properties for compatibility
    toggle_key = property(lambda self: self.config['toggle_key'])
    audio_device = property(lambda self: self.config['audio_device'])
    audio_gain = property(lambda self: self.config['audio_gain'])
    whisper_model = property(lambda self: self.config['whisper_model'])
    silence_threshold = property(lambda self: self.config['silence_threshold'])
    audio_threshold = property(lambda self: self.config['audio_threshold'])
    start_minimized = property(lambda self: self.config['start_minimized'])
    show_notifications = property(lambda self: self.config['show_notifications'])
    play_sounds = property(lambda self: self.config['play_sounds'])
    auto_start = property(lambda self: self.config['auto_start'])
    language = property(lambda self: self.config['language'])
    continuous_mode = property(lambda self: self.config.get('continuous_mode', False))
    output_method = property(lambda self: self.config.get('output_method', 'type'))
    device = property(lambda self: self.config.get('device', 'auto'))
    compute_type = property(lambda self: self.config.get('compute_type', 'auto'))
    gpu_memory_limit = property(lambda self: self.config.get('gpu_memory_limit', 0))


class HotkeyDialog(Gtk.Dialog):
    """Dialog to capture a hotkey press."""
    
    def __init__(self, parent):
        super().__init__(title="Set Hotkey", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self.captured_key = None
        self.set_default_size(300, 150)
        
        # Create content area
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_left(20)
        vbox.set_margin_right(20)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        
        label = Gtk.Label(label="Press any key to set as hotkey:")
        vbox.pack_start(label, False, False, 0)
        
        self.key_label = Gtk.Label(label="Waiting for key press...")
        self.key_label.set_markup("<i>Waiting for key press...</i>")
        vbox.pack_start(self.key_label, False, False, 0)
        
        info_label = Gtk.Label(label="Common keys: F1-F12, Ctrl+key, Alt+key")
        info_label.set_markup("<small>Common keys: F1-F12, Ctrl+key, Alt+key</small>")
        vbox.pack_start(info_label, False, False, 0)
        
        self.get_content_area().add(vbox)
        
        # Connect key press event
        self.connect("key-press-event", self.on_key_press)
        self.set_can_focus(True)
        
        self.show_all()
    
    def on_key_press(self, widget, event):
        """Capture key press with universal keyboard library."""
        try:
            from gi.repository import Gdk
            key_name = Gdk.keyval_name(event.keyval)
        except:
            key_name = str(event.keyval)
        
        # Convert to keyboard library format
        key_mapping = {
            'F16': 'f16', 'F15': 'f15', 'F14': 'f14', 'F13': 'f13',
            'F12': 'f12', 'F11': 'f11', 'F10': 'f10', 'F9': 'f9',
            'F8': 'f8', 'F7': 'f7', 'F6': 'f6', 'F5': 'f5', 
            'F4': 'f4', 'F3': 'f3', 'F2': 'f2', 'F1': 'f1',
            'Pause': 'pause', 'Scroll_Lock': 'scroll lock',
            'Launch7': 'f16',  # Map Launch keys to F keys
            'Launch6': 'f15',
            'Launch5': 'f14',
        }
        
        # Get clean key name
        clean_key = key_mapping.get(key_name, key_name.lower())
        
        # Handle single letter keys
        if len(clean_key) == 1 and clean_key.isalpha():
            pass  # Keep as-is
        elif clean_key not in ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'pause', 'scroll lock']:
            # For unknown keys, try to use a sensible default
            clean_key = 'f16'
        
        # Store the keyboard library compatible key name
        self.captured_key = clean_key
        self.key_label.set_markup(f"<b>Captured: {key_name} → {clean_key}</b>")
        
        print(f"Key captured: {key_name} → {clean_key}")
        return True  # Stop event propagation
    


# Import the GUI module directly
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import working audio test features
from audio_test_standalone import StandaloneAudioTestDialog as AudioTestDialog, get_audio_devices_standalone as get_audio_devices
HAS_AUDIO_TEST = True


# Copy the SettingsWindow class to avoid imports
class SettingsWindow(Gtk.Window):
    """Settings window for Whisper Toggle."""
    
    def __init__(self, config, on_save_callback=None):
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
        notebook.append_page(self.create_performance_tab(), Gtk.Label(label="Performance"))
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
    
    def create_general_tab(self):
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
        
        self.continuous_mode_check = Gtk.CheckButton(label="Continuous mode (experimental - types as you speak)")
        self.continuous_mode_check.set_active(self.config.get('continuous_mode', False))
        ui_box.pack_start(self.continuous_mode_check, False, False, 0)
        
        # Output method selection
        output_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        output_label = Gtk.Label(label="Output method:")
        output_box.pack_start(output_label, False, False, 0)
        
        self.output_combo = Gtk.ComboBoxText()
        self.output_combo.append("type", "Type text (slower)")
        self.output_combo.append("clipboard", "Copy to clipboard only")
        self.output_combo.append("paste", "Copy and auto-paste (fastest)")
        self.output_combo.append("paste_ctrl_shift_v", "Copy and paste (Ctrl+Shift+V)")
        current_method = self.config.get('output_method', 'type')
        self.output_combo.set_active_id(current_method)
        output_box.pack_start(self.output_combo, False, False, 0)
        
        ui_box.pack_start(output_box, False, False, 0)
        
        return vbox
    
    def create_audio_tab(self):
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
        
        # Current gain display
        gain_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        mic_box.pack_start(gain_box, False, False, 0)
        
        gain_label = Gtk.Label(label="Current gain:", xalign=0)
        gain_box.pack_start(gain_label, False, False, 0)
        
        self.gain_display = Gtk.Label()
        gain_db = 20 * math.log10(max(self.config.audio_gain, 0.001))
        if gain_db >= 0:
            self.gain_display.set_markup(f"<b>+{gain_db:.0f} dB</b> ({self.config.audio_gain:.1f}x)")
        else:
            self.gain_display.set_markup(f"<b>{gain_db:.0f} dB</b> ({self.config.audio_gain:.1f}x)")
        gain_box.pack_start(self.gain_display, False, False, 0)
        
        # Test microphone button
        test_button = Gtk.Button(label="Test Microphone & Set Gain")
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
    
    def create_hotkey_tab(self):
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
    
    def create_performance_tab(self):
        """Create performance/GPU settings tab."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        
        # Device selection
        device_frame = Gtk.Frame(label="Processing Device")
        vbox.pack_start(device_frame, False, False, 0)
        
        device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        device_box.set_border_width(10)
        device_frame.add(device_box)
        
        # Get current device info
        try:
            from transcriber_simple import detect_optimal_device
            optimal_device, device_name = detect_optimal_device()
            has_gpu = optimal_device == 'cuda'
        except ImportError:
            optimal_device, device_name = 'cpu', 'CPU'
            has_gpu = False
        
        # Device selection combo
        self.device_combo = Gtk.ComboBoxText()
        self.device_combo.append("auto", f"Auto-detect (Currently: {device_name})")
        self.device_combo.append("cpu", "CPU Only")
        if has_gpu:
            self.device_combo.append("cuda", f"GPU (CUDA) - {device_name}")
        else:
            self.device_combo.append("cuda", "GPU (CUDA) - Not Available")
            # Disable CUDA option if not available
            model = self.device_combo.get_model()
            iter_cuda = model.get_iter_from_string("2")  # CUDA is the 3rd item (index 2)
            model.set_value(iter_cuda, 1, False)  # Make it insensitive
        
        current_device = self.config.get('device', 'auto')
        self.device_combo.set_active_id(current_device)
        device_box.pack_start(self.device_combo, False, False, 0)
        
        # Device status info
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        device_box.pack_start(status_box, False, False, 0)
        
        status_label = Gtk.Label(label="Status:")
        status_box.pack_start(status_label, False, False, 0)
        
        if has_gpu:
            try:
                import torch
                gpu_name = torch.cuda.get_device_name(0)
                memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                self.device_status = Gtk.Label()
                self.device_status.set_markup(f"✓ <b>{gpu_name}</b> ({memory_gb:.1f}GB VRAM)")
                self.device_status.get_style_context().add_class("dim-label")
            except ImportError:
                self.device_status = Gtk.Label(label="⚠ PyTorch not available")
        else:
            self.device_status = Gtk.Label(label="ℹ GPU not available")
        
        status_box.pack_start(self.device_status, False, False, 0)
        
        # Compute type selection
        compute_frame = Gtk.Frame(label="Compute Precision")
        vbox.pack_start(compute_frame, False, False, 0)
        
        compute_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        compute_box.set_border_width(10)
        compute_frame.add(compute_box)
        
        self.compute_combo = Gtk.ComboBoxText()
        self.compute_combo.append("auto", "Auto-select (Recommended)")
        self.compute_combo.append("int8", "INT8 - Fastest, less accurate")
        self.compute_combo.append("float16", "FLOAT16 - Balanced (GPU only)")
        self.compute_combo.append("float32", "FLOAT32 - Slowest, most accurate")
        
        current_compute = self.config.get('compute_type', 'auto')
        self.compute_combo.set_active_id(current_compute)
        compute_box.pack_start(self.compute_combo, False, False, 0)
        
        # Compute type info
        compute_info = Gtk.Label()
        compute_info.set_markup("<small><i>Auto-select chooses INT8 for CPU, FLOAT16 for GPU</i></small>")
        compute_info.set_xalign(0)
        compute_box.pack_start(compute_info, False, False, 0)
        
        # GPU Memory limit (only show if GPU available)
        if has_gpu:
            memory_frame = Gtk.Frame(label="GPU Memory Management")
            vbox.pack_start(memory_frame, False, False, 0)
            
            memory_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            memory_box.set_border_width(10)
            memory_frame.add(memory_box)
            
            # Memory limit slider
            mem_limit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            mem_limit_label = Gtk.Label(label="Memory limit (GB):")
            mem_limit_box.pack_start(mem_limit_label, False, False, 0)
            
            self.memory_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 24, 1)
            self.memory_scale.set_value(self.config.get('gpu_memory_limit', 0))
            self.memory_scale.set_draw_value(True)
            self.memory_scale.set_value_pos(Gtk.PositionType.RIGHT)
            self.memory_scale.connect("value-changed", self.on_memory_limit_changed)
            mem_limit_box.pack_start(self.memory_scale, True, True, 0)
            
            memory_box.pack_start(mem_limit_box, False, False, 0)
            
            # Memory info
            self.memory_info = Gtk.Label()
            self.update_memory_info()
            self.memory_info.set_xalign(0)
            memory_box.pack_start(self.memory_info, False, False, 0)
        
        # Performance tips
        tips_frame = Gtk.Frame(label="Performance Tips")
        vbox.pack_end(tips_frame, False, False, 0)
        
        tips_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        tips_box.set_border_width(10)
        tips_frame.add(tips_box)
        
        tips = [
            "• Use GPU (CUDA) for 10-20x faster transcription",
            "• FLOAT16 provides best speed/accuracy balance on GPU",
            "• Larger models (medium/large) benefit most from GPU acceleration",
            "• Set memory limit if running other GPU applications"
        ]
        
        for tip in tips:
            tip_label = Gtk.Label(label=tip)
            tip_label.set_xalign(0)
            tip_label.get_style_context().add_class("dim-label")
            tips_box.pack_start(tip_label, False, False, 0)
        
        return vbox
    
    def on_memory_limit_changed(self, scale):
        """Handle memory limit slider change."""
        if hasattr(self, 'memory_info'):
            self.update_memory_info()
    
    def update_memory_info(self):
        """Update memory limit info text."""
        if hasattr(self, 'memory_scale'):
            limit = int(self.memory_scale.get_value())
            if limit == 0:
                self.memory_info.set_markup("<small><i>0 = No limit (use all available GPU memory)</i></small>")
            else:
                self.memory_info.set_markup(f"<small><i>Limit GPU usage to {limit}GB</i></small>")
    
    def create_advanced_tab(self):
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
        
        # Open audio test dialog with current gain
        dialog = AudioTestDialog(self, device_index, self.config.audio_gain)
        response = dialog.run()
        
        # Get the selected gain from the dialog
        new_gain = dialog.selected_gain
        dialog.destroy()
        
        # Update the config with new gain
        if new_gain != self.config.audio_gain:
            self.config.set('audio_gain', new_gain)
            gain_db = 20 * math.log10(max(new_gain, 0.001))
            if gain_db >= 0:
                self.gain_display.set_markup(f"<b>+{gain_db:.0f} dB</b> ({new_gain:.1f}x)")
            else:
                self.gain_display.set_markup(f"<b>{gain_db:.0f} dB</b> ({new_gain:.1f}x)")
            
            # Show confirmation
            msg = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Gain Updated"
            )
            db_text = f"+{gain_db:.0f}" if gain_db >= 0 else f"{gain_db:.0f}"
            msg.format_secondary_text(f"Audio gain set to {db_text} dB ({new_gain:.1f}x)")
            msg.run()
            msg.destroy()
    
    def on_set_hotkey(self, button):
        """Set a new hotkey."""
        dialog = HotkeyDialog(self)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_key = dialog.captured_key
            if new_key:
                self.config.set('toggle_key', new_key)
                self.hotkey_label.set_markup(f"<b>{new_key}</b>")
                print(f"Hotkey changed to: {new_key}")
        
        dialog.destroy()
    
    def on_common_key_clicked(self, button, key_code):
        """Set a common hotkey."""
        self.config.set('toggle_key', key_code)
        self.hotkey_label.set_markup(f"<b>{key_code}</b>")
        print(f"Selected hotkey: {key_code}")
    
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
            print("Settings reset to defaults (demo mode)")
    
    def save_settings(self):
        """Save UI settings to config."""
        self.config.set('whisper_model', self.model_combo.get_active_id())
        self.config.set('language', self.language_combo.get_active_id())
        self.config.set('start_minimized', self.start_minimized_check.get_active())
        self.config.set('show_notifications', self.show_notifications_check.get_active())
        self.config.set('play_sounds', self.play_sounds_check.get_active())
        self.config.set('auto_start', self.auto_start_check.get_active())
        self.config.set('continuous_mode', self.continuous_mode_check.get_active())
        self.config.set('output_method', self.output_combo.get_active_id())
        
        device_id = self.mic_combo.get_active_id()
        if device_id == "-1":
            self.config.set('audio_device', None)
        else:
            self.config.set('audio_device', int(device_id))
        
        self.config.set('silence_threshold', self.silence_adjustment.get_value())
        self.config.set('audio_threshold', self.level_adjustment.get_value())
        
        # Audio gain is already set in on_test_microphone
        
        # Get hotkey from label
        hotkey = self.hotkey_label.get_text()
        if hotkey:
            self.config.set('toggle_key', hotkey)
        
        # Save GPU/Performance settings
        if hasattr(self, 'device_combo'):
            self.config.set('device', self.device_combo.get_active_id())
        if hasattr(self, 'compute_combo'):
            self.config.set('compute_type', self.compute_combo.get_active_id())
        if hasattr(self, 'memory_scale'):
            self.config.set('gpu_memory_limit', int(self.memory_scale.get_value()))
    
    def on_cancel_clicked(self, button):
        """Handle cancel button click."""
        self.close()
    
    def on_apply_clicked(self, button):
        """Handle apply button click."""
        self.save_settings()
        if self.on_save_callback:
            self.on_save_callback(self.config)
        print("Settings applied (demo mode)")
    
    def on_save_clicked(self, button):
        """Handle save button click."""
        self.save_settings()
        self.config.save()
        if self.on_save_callback:
            self.on_save_callback(self.config)
        print("Settings saved and closing window (demo mode)")
        self.close()


def main():
    """Run the demo."""
    print("=== Whisper Toggle Demo ===")
    print("This demo shows the beautiful GTK interface.")
    print(f"✓ Audio test available: {HAS_AUDIO_TEST}")
    print("✓ Your fifine Microphone should appear as device #1")
    print("\nOpening settings window...\n")
    
    config = DemoConfig()
    
    def on_save(config):
        print("\nSettings saved with values:")
        print(f"  Model: {config.whisper_model}")
        print(f"  Language: {config.language}")
        print(f"  Toggle key: {config.toggle_key}")
        print(f"  Audio device: {config.audio_device}")
    
    window = SettingsWindow(config, on_save_callback=on_save)
    window.connect("destroy", Gtk.main_quit)
    
    Gtk.main()
    
    print("\nDemo complete!")


if __name__ == "__main__":
    main()