#!/bin/bash
# Whisper Toggle Installation Script

set -e

echo "🎤 Whisper Toggle Installation Script"
echo "====================================="

# Check if running on supported system
if ! command -v systemctl &> /dev/null; then
    echo "❌ Error: systemd is required but not found"
    exit 1
fi

if [[ "$XDG_SESSION_TYPE" != "wayland" ]]; then
    echo "⚠️  Warning: This tool is designed for Wayland. X11 may work but is not tested."
fi

# Check for required system packages
echo "📦 Checking system dependencies..."

MISSING_PACKAGES=()

if ! command -v python3 &> /dev/null; then
    MISSING_PACKAGES+=("python3")
fi

if ! command -v pip3 &> /dev/null; then
    MISSING_PACKAGES+=("python3-pip")
fi

if ! python3 -c "import venv" 2>/dev/null; then
    MISSING_PACKAGES+=("python3-venv")
fi

if ! command -v ydotool &> /dev/null; then
    MISSING_PACKAGES+=("ydotool")
fi

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "❌ Missing required packages: ${MISSING_PACKAGES[*]}"
    echo "Please install with:"
    echo "sudo apt install ${MISSING_PACKAGES[*]}"
    exit 1
fi

echo "✅ System dependencies found"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "whisper_env" ]; then
    python3 -m venv whisper_env
fi

source whisper_env/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install faster-whisper pyaudio evdev scipy numpy

echo "✅ Python dependencies installed"

# Test audio devices
echo "🎙️ Testing audio devices..."
python3 scripts/test_audio_devices.py

echo ""
echo "Please note the working device number above."
read -p "Enter the device number you want to use: " DEVICE_NUMBER

# Setup permissions
echo "🔐 Setting up permissions..."
if ! groups | grep -q input; then
    echo "Adding user to input group..."
    sudo usermod -a -G input $USER
    echo "⚠️  You'll need to log out and back in for this to take effect"
    NEED_LOGOUT=true
fi

# Copy files to home directory
echo "📁 Installing files..."
cp src/whisper_with_smart_indicators.py ~/
cp service/whisper-service.sh ~/
cp scripts/whisper-control.sh ~/

# Make scripts executable
chmod +x ~/whisper-service.sh ~/whisper-control.sh

# Update device number in service script
sed -i "s/python3 whisper_with_smart_indicators.py 8 9/python3 whisper_with_smart_indicators.py 8 $DEVICE_NUMBER/" ~/whisper-service.sh

# Install systemd service
echo "🔧 Installing system service..."
mkdir -p ~/.config/systemd/user
cp service/whisper-toggle.service ~/.config/systemd/user/

# Update service file paths
sed -i "s|/home/brad|$HOME|g" ~/.config/systemd/user/whisper-toggle.service

# Enable service
systemctl --user daemon-reload
systemctl --user enable whisper-toggle.service

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"

if [ "$NEED_LOGOUT" = true ]; then
    echo "1. Log out and back in to activate input group permissions"
    echo "2. Start the service: ./whisper-control.sh start"
else
    echo "1. Start the service: ./whisper-control.sh start"
fi

echo "3. Test by pressing the X button on your Keychron keyboard"
echo ""
echo "📋 Service management:"
echo "  ./whisper-control.sh start    # Start service"
echo "  ./whisper-control.sh stop     # Stop service"
echo "  ./whisper-control.sh status   # Check status"
echo "  ./whisper-control.sh logs     # View logs"
echo ""
echo "🎤 Happy transcribing!"