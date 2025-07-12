#!/bin/bash
# Check if ydotool is properly set up

echo "Checking ydotool setup..."
echo ""

# Check if ydotool is installed
if command -v ydotool &> /dev/null; then
    echo "✓ ydotool is installed"
else
    echo "✗ ydotool is NOT installed"
    echo "  Install with: sudo apt install ydotool"
    exit 1
fi

# Check if ydotoold service is running
if systemctl is-active --quiet ydotool; then
    echo "✓ ydotool service is running"
else
    echo "✗ ydotool service is NOT running"
    echo "  Start with: sudo systemctl start ydotool"
    echo "  Enable on boot: sudo systemctl enable ydotool"
fi

# Test ydotool
echo ""
echo "Testing ydotool..."
if timeout 2 ydotool type "test" &> /dev/null; then
    echo "✓ ydotool is working!"
else
    echo "✗ ydotool test failed"
    echo "  You may need to:"
    echo "  1. Start the service: sudo systemctl start ydotool"
    echo "  2. Add yourself to input group: sudo usermod -a -G input $USER"
    echo "  3. Log out and back in"
fi

echo ""
echo "For Whisper Toggle to type text, ydotool must be working properly."