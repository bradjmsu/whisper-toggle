#!/bin/bash
# Toggle whisper recording via D-Bus or signal
# This can be registered as a GNOME keyboard shortcut

# Find the running whisper-toggle process
PID=$(pgrep -f "whisper_toggle_gui.py")

if [ -z "$PID" ]; then
    echo "Whisper Toggle is not running"
    # Optionally start it
    # /home/brad/projects/whisper-toggle/run-gui.sh &
    exit 1
fi

# Send SIGUSR1 to toggle recording
kill -USR1 $PID

echo "Toggled recording (PID: $PID)"