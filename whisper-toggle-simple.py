#!/usr/bin/env python3
"""
Whisper Toggle - Simple version that works with minimal dependencies
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to run with whatever is available
print("Starting Whisper Toggle (Simple Mode)...")

try:
    # First try the full app
    from whisper_toggle.app import main
    main()
except ImportError as e:
    print(f"\nMissing dependency: {e}")
    print("\nTrying demo mode instead...")
    
    try:
        # Try to run the demo
        import demo_with_audio
        demo_with_audio.main()
    except ImportError:
        # Fall back to basic demo
        try:
            import demo_gui
            demo_gui.main()
        except ImportError as e2:
            print(f"\nCannot run even in demo mode: {e2}")
            print("\nPlease install dependencies:")
            print("1. System packages:")
            print("   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
            print("   sudo apt install gir1.2-appindicator3-0.1 libgirepository1.0-dev")
            print("\n2. Python packages:")
            print("   pip install pyyaml")
            print("   pip install pyaudio")
            print("   pip install faster-whisper evdev scipy numpy")
            sys.exit(1)