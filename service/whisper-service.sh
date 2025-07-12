#!/bin/bash
# Whisper Toggle Service Launcher

# Set up environment
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export HOME=/home/brad

# Wait for graphical session and audio to be ready
sleep 5

# Change to home directory
cd /home/brad

# Activate virtual environment
source whisper_env/bin/activate

# Wait for audio devices to be available  
echo "Checking for audio device..."
for i in {1..10}; do
    if python3 -c "
import pyaudio
try:
    p = pyaudio.PyAudio()
    info = p.get_device_info_by_index(9)
    p.terminate()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo "Audio device found, starting Whisper Toggle with Smart Indicators..."
        break
    fi
    echo "Waiting for audio device... ($i/10)"
    sleep 2
done

# Run with input group permissions
echo "Launching Whisper Toggle with Smart Indicators..."
sg input -c "python3 whisper_with_smart_indicators.py 8 9"