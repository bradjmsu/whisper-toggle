#!/usr/bin/env python3
"""
GTK-based keyboard monitoring that works like the settings dialog.
This approach detects special keys more reliably than pynput.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Keybinder', '3.0')
from gi.repository import Gtk, Gdk, GLib

try:
    from gi.repository import Keybinder
    HAS_KEYBINDER = True
except ImportError:
    HAS_KEYBINDER = False
    print("Warning: Keybinder not available - install gir1.2-keybinder-3.0")


class UniversalKeyboardMonitor:
    """Universal keyboard monitoring using GTK/Keybinder."""
    
    def __init__(self, callback):
        self.callback = callback
        self.monitoring = False
        
    def start_monitoring(self, key_name):
        """Start monitoring for a specific key."""
        print(f"\n=== GTK KEYBOARD MONITORING ===")
        
        if HAS_KEYBINDER:
            # Use Keybinder for global hotkeys (most reliable)
            try:
                Keybinder.init()
                
                # Map key names to Keybinder format
                key_mapping = {
                    'f16': '<F16>',
                    'f15': '<F15>',
                    'f14': '<F14>',
                    'f13': '<F13>',
                    'pause': 'Pause',
                    'c': 'c',
                    'p': 'p'
                }
                
                keybind = key_mapping.get(key_name, f'<{key_name.upper()}>')
                
                print(f"Registering global hotkey: {keybind}")
                success = Keybinder.bind(keybind, self._on_hotkey, None)
                
                if success:
                    print(f"✓ Global hotkey '{keybind}' registered successfully")
                    self.monitoring = True
                else:
                    print(f"✗ Failed to register '{keybind}'")
                    # Try without brackets
                    keybind2 = key_name.upper()
                    success = Keybinder.bind(keybind2, self._on_hotkey, None)
                    if success:
                        print(f"✓ Registered as '{keybind2}'")
                        self.monitoring = True
                    else:
                        print("✗ Keybinder registration failed")
                
            except Exception as e:
                print(f"Keybinder error: {e}")
        else:
            print("✗ Keybinder not available - install gir1.2-keybinder-3.0")
            print("  sudo apt-get install gir1.2-keybinder-3.0")
            
            # Fallback to window key events (less reliable but works)
            self._create_invisible_window(key_name)
    
    def _on_hotkey(self, keystring, user_data):
        """Handle global hotkey press."""
        print(f"\n>>> GLOBAL HOTKEY PRESSED: {keystring} <<<")
        GLib.idle_add(self.callback)
    
    def _create_invisible_window(self, key_name):
        """Create invisible window to capture key events as fallback."""
        print("Using fallback window-based key detection")
        
        self.window = Gtk.Window()
        self.window.set_default_size(1, 1)
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_keep_above(True)
        
        # Make it nearly invisible
        self.window.set_opacity(0.01)
        self.window.move(-100, -100)
        
        def on_key_press(widget, event):
            key_name_pressed = Gdk.keyval_name(event.keyval).lower()
            if key_name_pressed == key_name or key_name_pressed == f'f{key_name}':
                print(f"\n>>> WINDOW HOTKEY DETECTED: {key_name_pressed} <<<")
                GLib.idle_add(self.callback)
                return True
            return False
        
        self.window.connect("key-press-event", on_key_press)
        self.window.show()
        print(f"✓ Window-based monitoring for '{key_name}' started")
    
    def stop_monitoring(self):
        """Stop keyboard monitoring."""
        if HAS_KEYBINDER and self.monitoring:
            try:
                Keybinder.unbind_all()
                print("✓ Keybinder stopped")
            except:
                pass
        
        if hasattr(self, 'window'):
            self.window.destroy()
            print("✓ Window monitoring stopped")


# Test if this module works
if __name__ == "__main__":
    print("Testing GTK keyboard monitoring...")
    
    def test_callback():
        print("HOTKEY ACTIVATED!")
    
    monitor = UniversalKeyboardMonitor(test_callback)
    monitor.start_monitoring('f16')
    
    print("\nPress F16 to test (Ctrl+C to quit)...")
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nStopping...")
        monitor.stop_monitoring()