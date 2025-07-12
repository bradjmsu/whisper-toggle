#!/bin/bash
# One-click installer for Whisper Toggle

# Don't exit on errors - we'll handle them gracefully
set +e

echo "=== Whisper Toggle Installer ==="
echo ""
echo "This will install all required dependencies and set up Whisper Toggle."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "Please do not run as root. The script will ask for sudo when needed."
   exit 1
fi

# Prompt for password upfront
echo "Installing system packages (requires sudo)..."
sudo echo "Got sudo access, continuing..."

# Install system dependencies
echo "Installing system packages..."
# Update package list, ignoring repository errors
sudo apt update 2>/dev/null || echo "Some repositories failed, continuing..."

# Install packages one by one to handle failures gracefully
packages=(
    "python3-gi"
    "python3-gi-cairo" 
    "gir1.2-appindicator3-0.1"
    "python3-pip"
    "python3-venv"
    "alsa-utils"
    "ydotool"
    "python3-dev"
    "build-essential"
)

for package in "${packages[@]}"; do
    echo "Installing $package..."
    if ! sudo apt install -y "$package" 2>/dev/null; then
        echo "Warning: Failed to install $package, trying to continue..."
    fi
done

# Create virtual environment with system packages
echo "Creating virtual environment..."
rm -rf venv  # Remove if exists
python3 -m venv venv --system-site-packages

# Install Python packages
echo "Installing Python packages..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    echo "Installing evdev..."
    pip install evdev || echo "Warning: evdev install failed"
    echo "Installing faster-whisper..."
    pip install faster-whisper || echo "Warning: faster-whisper install failed"
else
    echo "Error: Virtual environment creation failed"
    exit 1
fi

# Set up permissions for input devices (for keyboard monitoring without sudo)
echo "Setting up permissions..."
sudo usermod -a -G input $USER

# Create desktop entry
echo "Creating desktop entry..."
cat > ~/.local/share/applications/whisper-toggle.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Whisper Toggle
Comment=Voice transcription with hardware toggle
Exec=$PWD/run-gui.sh
Icon=audio-input-microphone
Terminal=false
Categories=Utility;AudioVideo;
StartupNotify=false
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "To run Whisper Toggle:"
echo "  1. Log out and log back in (for input group permissions)"
echo "  2. Run: ./run-gui.sh"
echo "  3. Or search for 'Whisper Toggle' in your applications menu"
echo ""
echo "Usage:"
echo "  - The app runs in the system tray (microphone icon)"
echo "  - Press F16 to start/stop recording"
echo "  - Right-click tray icon for settings"
echo ""
echo "Note: First run will download the Whisper model (~150MB)"