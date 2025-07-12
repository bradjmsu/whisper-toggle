#!/usr/bin/env python3
"""
Wayland-compatible keyboard monitoring.
Uses systemd/logind session API for global hotkeys on Wayland.
"""

import subprocess
import os

def check_wayland():
    """Check if running on Wayland."""
    session_type = os.environ.get('XDG_SESSION_TYPE', '')
    wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
    
    print(f"Session type: {session_type}")
    print(f"Wayland display: {wayland_display}")
    
    return session_type == 'wayland' or wayland_display

def get_available_methods():
    """Check which global hotkey methods are available on Wayland."""
    methods = []
    
    # Method 1: evdev (requires input group)
    try:
        import evdev
        devices = list(evdev.list_devices())
        if devices:
            methods.append("evdev (direct input access)")
    except:
        pass
    
    # Method 2: libinput via subprocess
    try:
        result = subprocess.run(['libinput', 'list-devices'], capture_output=True)
        if result.returncode == 0:
            methods.append("libinput (may need root)")
    except:
        pass
    
    # Method 3: Desktop Environment integration
    de = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    if 'gnome' in de:
        methods.append("GNOME Shell extension API")
    elif 'kde' in de:
        methods.append("KDE global shortcuts")
    
    # Method 4: Wayland protocols
    if check_wayland():
        methods.append("Wayland compositor shortcuts (DE-specific)")
    
    return methods

# Test available methods
if __name__ == "__main__":
    print("=== Wayland Keyboard Detection ===")
    
    if check_wayland():
        print("✓ Running on Wayland")
    else:
        print("✗ Not running on Wayland")
    
    print("\nAvailable methods:")
    methods = get_available_methods()
    for method in methods:
        print(f"  - {method}")
    
    print("\nRecommendations for Wayland:")
    print("1. Use evdev directly (current fallback)")
    print("2. Register shortcut in GNOME Settings")
    print("3. Use a dedicated Wayland input method")
    print("4. Run with XWayland for compatibility")