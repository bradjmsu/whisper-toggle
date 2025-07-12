#!/usr/bin/env python3
"""
Whisper Toggle with GUI - No sudo required version
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import subprocess
import threading
import queue
import time
import os
import sys
import signal

# Import our GUI components
from demo_standalone import SettingsWindow
from audio_test_standalone import StandaloneAudioTestDialog
from transcriber_simple import SimpleTranscriber
from config import Config

class WhisperToggleGUI:
    """Main application with system tray and transcription."""
    
    def __init__(self):
        self.running = True
        self.transcribing = False
        self.continuous_active = False
        self.audio_queue = queue.Queue()
        self.config = Config()
        
        # Create transcriber
        self.transcriber = SimpleTranscriber(self.config)
        
        # Try to import optional components
        self.setup_optional_imports()
        
        # Create status icon (system tray)
        self.create_tray_icon()
        
        # Setup signal handler for external toggle
        signal.signal(signal.SIGUSR1, self._handle_signal_toggle)
        
        # Start keyboard monitoring thread
        self.start_keyboard_monitor()
    
    def setup_optional_imports(self):
        """Import optional components with fallbacks."""
        self.has_transcription = False
        self.has_audio = False
        
        # Try to import transcription components
        try:
            from faster_whisper import WhisperModel
            self.WhisperModel = WhisperModel
            self.has_transcription = True
        except ImportError:
            print("Whisper not available - install faster-whisper for transcription")
        
        # Try to import audio components
        try:
            import pyaudio
            import numpy as np
            self.pyaudio = pyaudio
            self.np = np
            self.has_audio = True
        except ImportError:
            print("Audio not available - install pyaudio and numpy for recording")
    
    # load_config method removed - using Config class instead
    
    def create_tray_icon(self):
        """Create system tray icon."""
        try:
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import AppIndicator3
            
            self.indicator = AppIndicator3.Indicator.new(
                "whisper-toggle",
                "audio-input-microphone",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            
            # Create menu
            menu = Gtk.Menu()
            
            # Toggle recording item
            self.toggle_item = Gtk.MenuItem(label="Start Recording (F16)")
            self.toggle_item.connect("activate", lambda w: self.toggle_transcription())
            menu.append(self.toggle_item)
            
            # Settings item
            settings_item = Gtk.MenuItem(label="Settings")
            settings_item.connect("activate", self.show_settings)
            menu.append(settings_item)
            
            menu.append(Gtk.SeparatorMenuItem())
            
            # Quit item
            quit_item = Gtk.MenuItem(label="Quit")
            quit_item.connect("activate", self.quit)
            menu.append(quit_item)
            
            menu.show_all()
            self.indicator.set_menu(menu)
            
        except Exception as e:
            print(f"System tray not available: {e}")
            print("\nTo use system tray, install:")
            print("  sudo apt install gir1.2-appindicator3-0.1")
            # Don't create fallback window - just show instructions
    
    def update_toggle_menu_item(self):
        """Update the toggle menu item text based on state."""
        if hasattr(self, 'toggle_item'):
            if self.transcribing:
                self.toggle_item.set_label("Stop Recording (F16)")
            else:
                self.toggle_item.set_label("Start Recording (F16)")
    
    def show_settings(self, widget):
        """Show settings window."""
        # Use the config object directly since it already has the right interface
        config_wrapper = self.config
        
        def on_save(config):
            # Update our config - the config wrapper has already updated our self.config
            # Just save it to file
            saved = self.config.save()
            if saved:
                print("Settings saved successfully!")
            else:
                print("Error saving settings!")
            
            # Restart transcription with new settings
            self.restart_transcription()
            
            # Restart keyboard monitoring with new hotkey
            self.restart_keyboard_monitoring()
        
        window = SettingsWindow(config_wrapper, on_save_callback=on_save)
        window.present()
    
    def test_microphone(self, widget):
        """Show microphone test dialog."""
        parent = getattr(self, 'window', None)
        dialog = StandaloneAudioTestDialog(
            parent,
            self.config.get('audio_device'),
            self.config.get('audio_gain', 1.0)
        )
        response = dialog.run()
        
        # Update gain if changed
        if dialog.selected_gain != self.config['audio_gain']:
            self.config['audio_gain'] = dialog.selected_gain
        
        dialog.destroy()
    
    def start_keyboard_monitor(self):
        """Start keyboard monitoring with Wayland support."""
        print("\n=== KEYBOARD MONITORING ===")
        
        # Check if on Wayland
        session_type = os.environ.get('XDG_SESSION_TYPE', '')
        print(f"Session type: {session_type}")
        
        # Get configured key
        toggle_key = self.config.get('toggle_key', 'f16')
        
        # Convert to clean format
        key_mapping = {
            'KEY_F16': 'f16', 'KEY_F15': 'f15', 'KEY_F14': 'f14',
            '269025095': 'f16', '269025094': 'f15', '99': 'c', '112': 'p'
        }
        
        key_name = key_mapping.get(str(toggle_key), str(toggle_key).lower().replace('key_', ''))
        print(f"Configured hotkey: {key_name}")
        
        if session_type == 'wayland':
            print("⚠ Running on Wayland - using evdev for keyboard monitoring")
            # For Wayland, go straight to evdev
            self._start_evdev_monitoring(key_name)
        else:
            # Try Keybinder for X11
            try:
                from gi.repository import Keybinder
                Keybinder.init()
                
                keybind_mapping = {
                    'f16': '<F16>', 'f15': '<F15>', 'f14': '<F14>', 'f13': '<F13>',
                    'pause': 'Pause', 'c': 'c', 'p': 'p'
                }
                
                keybind = keybind_mapping.get(key_name, f'<{key_name.upper()}>')
                
                def on_hotkey(keystring):
                    print(f"\n>>> HOTKEY PRESSED: {keystring} <<<")
                    GLib.idle_add(self.toggle_transcription)
                
                success = Keybinder.bind(keybind, on_hotkey)
                
                if success:
                    print(f"✓ Global hotkey '{keybind}' registered (X11)")
                    return
                    
            except Exception as e:
                print(f"✗ Keybinder failed: {e}")
            
            # Fallback to evdev
            self._start_evdev_monitoring(key_name)
    
    def _start_evdev_monitoring(self, key_name):
        """Start evdev monitoring (works on Wayland with input group)."""
        try:
            import evdev
            print("Using evdev for keyboard monitoring")
            
            # Map key names to evdev codes (corrected based on actual keycodes)
            key_to_code = {
                'f16': 186,  # Launch7 on your Keychron
                'f15': 185,  # Launch6 on your Keychron
                'f14': 184,  # Launch5 on your Keychron
                'f13': 183,  # Launch4 on your Keychron
                'f12': 88, 'f11': 87, 'f10': 68, 'f9': 67,
                'f8': 66, 'f7': 65, 'f6': 64, 'f5': 63,
                'f4': 62, 'f3': 61, 'f2': 60, 'f1': 59,
                'c': 46, 'p': 25, 'pause': 119
            }
            
            target_code = key_to_code.get(key_name, 194)
            print(f"Looking for key code: {target_code}")
            
            # Find keyboard devices
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            keyboards = []
            
            for device in devices:
                caps = device.capabilities(verbose=False)
                if evdev.ecodes.EV_KEY in caps:
                    # Check if it has KEY_A (30) - indicates it's a keyboard
                    if 30 in caps[evdev.ecodes.EV_KEY]:
                        keyboards.append(device)
                        print(f"Found keyboard: {device.name}")
            
            if not keyboards:
                print("✗ No keyboards found via evdev")
                print("Make sure you're in the 'input' group: sudo usermod -a -G input $USER")
                return
            
            def monitor_thread():
                print(f"✓ Monitoring {len(keyboards)} keyboard(s) for key code {target_code}")
                
                # Monitor all keyboards
                while self.running:
                    for device in keyboards:
                        try:
                            # Non-blocking read
                            for event in device.read():
                                if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                                    if event.code == target_code:
                                        print(f"\n>>> HOTKEY PRESSED: {key_name} (code {event.code}) <<<")
                                        GLib.idle_add(self.toggle_transcription)
                                    # Debug: show high keycodes
                                    elif event.code > 180:
                                        print(f"[DEBUG] High keycode pressed: {event.code}")
                        except BlockingIOError:
                            # No events available, continue
                            pass
                        except Exception as e:
                            print(f"Device read error: {e}")
                    
                    # Small sleep to prevent CPU spinning
                    time.sleep(0.01)
            
            self.keyboard_thread = threading.Thread(target=monitor_thread, daemon=True)
            self.keyboard_thread.start()
            print("✓ evdev monitoring started (Wayland compatible)")
            
        except Exception as e:
            print(f"✗ evdev monitoring failed: {e}")
            print("⚠ Hotkeys disabled - use system tray menu or GNOME Settings")
            print("\nAlternative: Register a custom shortcut in GNOME Settings:")
            print("  1. Open Settings → Keyboard → View and Customize Shortcuts")
            print("  2. Add custom shortcut for: /home/brad/projects/whisper-toggle/toggle.sh")
            print("  3. Assign your preferred key")
    
    def restart_keyboard_monitoring(self):
        """Restart keyboard monitoring with new settings."""
        print("\n=== RESTARTING KEYBOARD MONITORING ===")
        
        # Stop current monitoring
        if hasattr(self, 'keyboard_thread') and self.keyboard_thread and self.keyboard_thread.is_alive():
            self.running = False  # Signal thread to stop
            self.keyboard_thread.join(timeout=1)  # Wait for thread to stop
            self.running = True  # Re-enable for new thread
        
        # Restart monitoring with new key
        self.start_keyboard_monitor()
    
    def _handle_signal_toggle(self, signum, frame):
        """Handle external toggle signal (SIGUSR1)."""
        print("\n>>> EXTERNAL TOGGLE SIGNAL RECEIVED <<<")
        GLib.idle_add(self.toggle_transcription)
    
    def toggle_transcription(self):
        """Toggle transcription on/off."""
        continuous_mode = self.config.get('continuous_mode', False)
        
        self.transcribing = not self.transcribing
        
        if self.transcribing:
            print("\n=== STARTING RECORDING ===")
            print(f"Mode: {'Continuous' if continuous_mode else 'Push-to-talk'}")
            print(f"Audio device: {self.config.get('audio_device')}")
            print(f"Whisper model: {self.config.get('whisper_model')}")
            print(f"Language: {self.config.get('language')}")
            print(f"Audio gain: {self.config.get('audio_gain')}x")
            
            self.update_status("Listening...")
            self.update_toggle_menu_item()
            
            if continuous_mode:
                self.start_continuous_recording()
            else:
                self.start_recording()
            
            # Play start sound
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/message.oga'], 
                         capture_output=True)
        else:
            print("\n=== STOPPING RECORDING ===")
            self.update_status("Processing..." if not continuous_mode else "Ready")
            self.update_toggle_menu_item()
            
            if continuous_mode:
                self.stop_continuous_recording()
            else:
                self.stop_recording()
            
            # Play stop sound
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'], 
                         capture_output=True)
    
    def update_status(self, status):
        """Update status in UI."""
        # Update tray icon if available
        if hasattr(self, 'indicator'):
            if status == "Listening...":
                self.indicator.set_icon("audio-input-microphone-high")
            elif status == "Processing..." or status == "Transcribing...":
                self.indicator.set_icon("media-playback-pause")
            else:
                self.indicator.set_icon("audio-input-microphone")
    
    def start_recording(self):
        """Start audio recording."""
        print("Starting audio recording...")
        self.transcriber.start_recording()
    
    def stop_recording(self):
        """Stop audio recording and transcribe."""
        def process_audio():
            # Stop recording and get audio data
            audio_data = self.transcriber.stop_recording()
            
            if audio_data:
                # Update status
                GLib.idle_add(self.update_status, "Transcribing...")
                
                # Transcribe
                text = self.transcriber.transcribe_audio(audio_data)
                
                if text:
                    print(f"\n=== TRANSCRIPTION RESULT ===")
                    print(f"Text: {text}")
                    print(f"Length: {len(text)} characters")
                    # Output the text (type or clipboard)
                    GLib.idle_add(self.output_text, text)
                else:
                    print("\n=== NO TRANSCRIPTION RESULT ===")
                    print("Possible issues:")
                    print("- No speech detected")
                    print("- Audio too quiet")
                    print("- Wrong microphone selected")
            else:
                print("\n=== NO AUDIO DATA ===")
                print("Recording failed - check microphone")
                
            # Reset status
            GLib.idle_add(self.update_status, "Ready")
            self.transcribing = False
            GLib.idle_add(self.update_toggle_menu_item)
        
        # Process in background thread
        threading.Thread(target=process_audio, daemon=True).start()
    
    def start_continuous_recording(self):
        """Start continuous recording with real-time transcription."""
        print("Starting continuous recording...")
        self.continuous_active = True
        self.transcriber.start_recording()
        
        # Start continuous processing thread
        threading.Thread(target=self._continuous_processing_loop, daemon=True).start()
    
    def stop_continuous_recording(self):
        """Stop continuous recording."""
        print("Stopping continuous recording...")
        self.continuous_active = False
        self.transcriber.stop_recording()
        self.transcribing = False
        self.update_status("Ready")
    
    def _continuous_processing_loop(self):
        """Process audio in overlapping chunks for continuous transcription."""
        import time
        
        chunk_interval = 3  # Process every 3 seconds for better responsiveness
        last_transcription = ""
        
        while self.continuous_active and self.transcribing:
            time.sleep(chunk_interval)
            
            if not self.continuous_active or not self.transcribing:
                break
            
            # Get recent audio (last ~5 seconds with overlap)
            if hasattr(self.transcriber, 'audio_data') and self.transcriber.audio_data:
                if len(self.transcriber.audio_data) > 150:  # At least ~3 seconds of data
                    # Get the last 250 chunks (~5 seconds) for context
                    recent_chunks = self.transcriber.audio_data[-250:]
                    audio_data = b''.join(recent_chunks)
                    
                    print(f"Processing recent audio: {len(audio_data)} bytes")
                    
                    def process_recent():
                        nonlocal last_transcription
                        text = self.transcriber.transcribe_audio(audio_data)
                        if text and text.strip():
                            text = text.strip()
                            
                            # Remove overlap with previous transcription
                            if last_transcription:
                                # Find where new text starts by removing common prefix
                                words_old = last_transcription.split()
                                words_new = text.split()
                                
                                # Find the longest common suffix of old with prefix of new
                                overlap_found = False
                                for i in range(min(10, len(words_old))):  # Check last 10 words
                                    suffix = " ".join(words_old[-i-1:]) if i > 0 else words_old[-1]
                                    if text.startswith(suffix):
                                        # Remove the overlapping part
                                        text = text[len(suffix):].strip()
                                        overlap_found = True
                                        break
                                
                                # If no overlap found but text is very similar, skip it
                                if not overlap_found and text in last_transcription:
                                    return
                            
                            if text:  # Only output if there's new content
                                print(f"New text: '{text}'")
                                last_transcription = last_transcription + " " + text if last_transcription else text
                                # Keep only recent words to prevent memory buildup
                                words = last_transcription.split()
                                if len(words) > 50:
                                    last_transcription = " ".join(words[-30:])
                                
                                # Continuous mode always types directly
                                GLib.idle_add(self.type_text, text + " ")
                    
                    threading.Thread(target=process_recent, daemon=True).start()
    
    def output_text(self, text):
        """Output text using either typing or clipboard based on settings."""
        output_method = self.config.get('output_method', 'type')
        print(f"\n=== OUTPUT TEXT ===")
        print(f"Method: {output_method}")
        print(f"Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        if output_method == 'clipboard':
            print("→ Copying to clipboard")
            self.copy_to_clipboard(text)
        elif output_method == 'paste':
            print("→ Copy and paste")
            self.copy_and_paste(text)
        else:
            print("→ Typing text")
            self.type_text(text)
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            # Use xclip or wl-copy depending on environment
            import subprocess
            print(f"\n=== COPYING TO CLIPBOARD ===")
            print(f"Copying: {text[:50]}..." if len(text) > 50 else f"Copying: {text}")
            
            # Try wl-copy first (Wayland), then xclip (X11)
            try:
                subprocess.run(['wl-copy'], input=text.encode(), check=True)
                print("✓ Copied to clipboard (Wayland)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
                    print("✓ Copied to clipboard (X11)")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("❌ No clipboard tool available (install wl-clipboard or xclip)")
                    # Fallback to typing
                    self.type_text(text)
        except Exception as e:
            print(f"❌ Clipboard error: {e}")
            # Fallback to typing
            self.type_text(text)
    
    def copy_and_paste(self, text):
        """Copy text to clipboard and auto-paste it."""
        try:
            import subprocess
            print(f"\n=== COPY AND PASTE ===")
            print(f"Processing: {text[:50]}..." if len(text) > 50 else f"Processing: {text}")
            
            # First copy to clipboard
            try:
                subprocess.run(['wl-copy'], input=text.encode(), check=True)
                print("✓ Copied to clipboard (Wayland)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
                    print("✓ Copied to clipboard (X11)")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("❌ No clipboard tool available")
                    # Fallback to typing
                    self.type_text(text)
                    return
            
            # Small delay to ensure clipboard is updated
            import time
            time.sleep(0.1)
            
            # Now simulate Ctrl+V to paste
            try:
                # Use ydotool to simulate Ctrl+V
                subprocess.run(['ydotool', 'key', 'ctrl+v'], check=True)
                print("✓ Auto-pasted with Ctrl+V")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Auto-paste failed - ydotool issue")
                print("Text is in clipboard, paste manually with Ctrl+V")
                
        except Exception as e:
            print(f"❌ Copy and paste error: {e}")
            # Fallback to typing
            self.type_text(text)
    
    def type_text(self, text):
        """Type text using ydotool."""
        print(f"\n=== TYPING TEXT ===")
        print(f"Attempting to type: {text[:50]}..." if len(text) > 50 else f"Attempting to type: {text}")
        
        try:
            result = subprocess.run(['ydotool', 'type', text], 
                                  capture_output=True, text=True, check=True)
            print("✓ Text typed successfully!")
            if result.stdout:
                print(f"Output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to type text: {e}")
            print(f"Error output: {e.stderr}")
            print("Is ydotoold service running? Try: sudo systemctl start ydotool")
        except FileNotFoundError:
            print("✗ ydotool not found!")
            print("Install with: sudo apt install ydotool")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    def start_transcription_thread(self):
        """Start the transcription worker thread."""
        # Would implement actual transcription here
        pass
    
    def restart_transcription(self):
        """Restart transcription with new settings."""
        print("Restarting transcription with new settings...")
        # Update transcriber config
        self.transcriber.config = self.config
        print(f"Updated model: {self.config.get('whisper_model')}")
        print(f"Updated language: {self.config.get('language')}")
        print(f"Updated audio device: {self.config.get('audio_device')}")
    
    def quit(self, widget=None):
        """Quit the application."""
        self.running = False
        Gtk.main_quit()


def main():
    """Main entry point."""
    print("\n" + "="*50)
    print("WHISPER TOGGLE - Real-time Voice Transcription")
    print("="*50)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nPress F16 to start/stop recording")
    print("Check system tray for menu options")
    print("\nMonitoring console output...\n")
    
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Create and run application
    app = WhisperToggleGUI()
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()