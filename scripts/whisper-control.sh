#!/bin/bash
# Whisper Toggle Service Control

case "$1" in
    start)
        echo "Starting Whisper Toggle service..."
        systemctl --user start whisper-toggle.service
        ;;
    stop)
        echo "Stopping Whisper Toggle service..."
        systemctl --user stop whisper-toggle.service
        ;;
    restart)
        echo "Restarting Whisper Toggle service..."
        systemctl --user restart whisper-toggle.service
        ;;
    status)
        systemctl --user status whisper-toggle.service
        ;;
    logs)
        journalctl --user -u whisper-toggle.service -f
        ;;
    enable)
        echo "Enabling Whisper Toggle to start on login..."
        systemctl --user enable whisper-toggle.service
        ;;
    disable)
        echo "Disabling Whisper Toggle auto-start..."
        systemctl --user disable whisper-toggle.service
        ;;
    manual)
        echo "Running Whisper Toggle manually..."
        cd /home/brad
        source whisper_env/bin/activate
        sg input -c "python3 whisper_gnome_indicator.py"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|enable|disable|manual}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the service"
        echo "  stop     - Stop the service" 
        echo "  restart  - Restart the service"
        echo "  status   - Show service status"
        echo "  logs     - Show service logs (follow mode)"
        echo "  enable   - Enable auto-start on login"
        echo "  disable  - Disable auto-start"
        echo "  manual   - Run manually (for testing)"
        exit 1
        ;;
esac