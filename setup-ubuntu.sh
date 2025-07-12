#!/bin/bash
# Setup script for Ubuntu/Debian systems

echo "=== Whisper Toggle Setup for Ubuntu ==="
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "Please run this script as a normal user (not root)"
   echo "The script will use sudo when needed"
   exit 1
fi

echo "This script will install required system packages."
echo "You'll be asked for your sudo password."
echo
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo
echo "Installing system packages..."
sudo apt update
sudo apt install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-appindicator3-0.1 \
    libgirepository1.0-dev \
    python3-dev \
    portaudio19-dev \
    python3-pyaudio \
    ydotool

echo
echo "Adding user to required groups..."
sudo usermod -a -G input,audio $USER

echo
echo "Creating virtual environment..."
python3 -m venv venv

echo
echo "Activating virtual environment..."
source venv/bin/activate

echo
echo "Installing Python packages (minimal)..."
pip install --upgrade pip
pip install pyyaml

echo
echo "=== Setup Complete ==="
echo
echo "To run Whisper Toggle:"
echo "  source venv/bin/activate"
echo "  ./whisper-toggle.py"
echo
echo "For full functionality, also install:"
echo "  pip install pyaudio faster-whisper evdev scipy numpy"
echo
echo "NOTE: You need to log out and back in for group changes to take effect!"