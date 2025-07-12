#!/bin/bash
# Simple installer that works without system packages

echo "=== Whisper Toggle Simple Installer ==="
echo ""
echo "Installing Python dependencies only..."
echo "(System GTK packages may need manual installation)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
rm -rf venv
python3 -m venv venv --system-site-packages

# Install Python packages
echo "Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install evdev faster-whisper

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "To run Whisper Toggle:"
echo "  ./run-gui.sh"
echo ""
echo "If you get GTK errors, install system packages:"
echo "  sudo apt install python3-gi python3-gi-cairo gir1.2-appindicator3-0.1"
echo ""
echo "Note: First run will download the Whisper model (~150MB)"