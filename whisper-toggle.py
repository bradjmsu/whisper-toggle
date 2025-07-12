#!/usr/bin/env python3
"""
Whisper Toggle - Main entry point

Run this file to start Whisper Toggle with GUI and system tray.
"""

import sys
import os

# Add the project directory to Python path for development
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from whisper_toggle.app import main

if __name__ == "__main__":
    print("Starting Whisper Toggle...")
    print("Note: Install all dependencies with: pip install -e .")
    print("For system tray support: sudo apt install gir1.2-appindicator3-0.1")
    print("-" * 60)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in a virtual environment")
        print("2. Install dependencies: pip install -e .")
        print("3. For audio issues: sudo usermod -a -G audio $USER")
        print("4. For keyboard access: sudo usermod -a -G input $USER")
        sys.exit(1)