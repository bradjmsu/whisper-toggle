#!/bin/bash
# Run Whisper Toggle

cd "$(dirname "$0")"

# Check if installed
if [ ! -d "venv" ]; then
    echo "Whisper Toggle is not installed."
    echo "Please run: ./install.sh"
    exit 1
fi

# Activate virtual environment and run
source venv/bin/activate
python whisper_toggle_gui.py