"""
System tray icon for Whisper Toggle.

Provides a tray icon with menu for quick access to controls.
"""

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
    HAS_APP_INDICATOR = True
except:
    HAS_APP_INDICATOR = False
from gi.repository import Gtk, GLib
import os
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class TrayIcon:
    """System tray icon with menu."""
    
    def __init__(self, 
                 on_toggle_callback: Optional[Callable] = None,
                 on_settings_callback: Optional[Callable] = None,
                 on_quit_callback: Optional[Callable] = None):
        """Initialize tray icon."""
        self.on_toggle_callback = on_toggle_callback
        self.on_settings_callback = on_settings_callback
        self.on_quit_callback = on_quit_callback
        
        self.is_recording = False
        
        # Create app indicator if available
        if HAS_APP_INDICATOR:
            self.indicator = AppIndicator3.Indicator.new(
                "whisper-toggle",
                "audio-input-microphone",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_menu(self.create_menu())
        else:
            logger.warning("AppIndicator3 not available - tray icon disabled")
            self.indicator = None
        
        # Set initial icon
        self.update_icon(False)
    
    def create_menu(self) -> Gtk.Menu:
        """Create the tray menu."""
        menu = Gtk.Menu()
        
        # Status item (non-clickable)
        self.status_item = Gtk.MenuItem(label="Status: Ready")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Toggle recording
        self.toggle_item = Gtk.MenuItem(label="Start Recording")
        self.toggle_item.connect("activate", self.on_toggle_clicked)
        menu.append(self.toggle_item)
        
        # Settings
        settings_item = Gtk.MenuItem(label="Settings...")
        settings_item.connect("activate", self.on_settings_clicked)
        menu.append(settings_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # About
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self.on_about_clicked)
        menu.append(about_item)
        
        # Quit
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_quit_clicked)
        menu.append(quit_item)
        
        menu.show_all()
        return menu
    
    def update_icon(self, is_recording: bool):
        """Update tray icon based on recording state."""
        self.is_recording = is_recording
        
        if not self.indicator:
            return
            
        if is_recording:
            # Try to use a custom icon if available
            icon_name = "audio-input-microphone-high"
            self.indicator.set_icon(icon_name)
            self.indicator.set_title("Whisper Toggle - Recording")
            self.status_item.set_label("Status: Recording...")
            self.toggle_item.set_label("Stop Recording")
        else:
            icon_name = "audio-input-microphone"
            self.indicator.set_icon(icon_name)
            self.indicator.set_title("Whisper Toggle - Ready")
            self.status_item.set_label("Status: Ready")
            self.toggle_item.set_label("Start Recording")
    
    def set_status(self, status: str):
        """Update status text."""
        self.status_item.set_label(f"Status: {status}")
    
    def on_toggle_clicked(self, item):
        """Handle toggle menu item click."""
        if self.on_toggle_callback:
            self.on_toggle_callback()
    
    def on_settings_clicked(self, item):
        """Handle settings menu item click."""
        if self.on_settings_callback:
            self.on_settings_callback()
    
    def on_about_clicked(self, item):
        """Handle about menu item click."""
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Whisper Toggle")
        dialog.set_version("1.0.0")
        dialog.set_copyright("© 2025 Brad Johnson")
        dialog.set_comments("Real-time voice transcription with hardware toggle")
        dialog.set_website("https://github.com/bradjohnson/whisper-toggle")
        dialog.set_website_label("GitHub Repository")
        dialog.set_license_type(Gtk.License.MIT_X11)
        
        # Try to set logo
        try:
            dialog.set_logo_icon_name("audio-input-microphone")
        except:
            pass
        
        dialog.run()
        dialog.destroy()
    
    def on_quit_clicked(self, item):
        """Handle quit menu item click."""
        if self.on_quit_callback:
            self.on_quit_callback()
        else:
            Gtk.main_quit()
    
    def show_notification(self, title: str, message: str, icon: str = "dialog-information"):
        """Show a notification."""
        try:
            # Use GLib for notifications
            notification = Gtk.Notification.new(title, message)
            notification.set_icon(icon)
            GLib.Application.get_default().send_notification(None, notification)
        except:
            # Fallback to command line notify-send
            try:
                import subprocess
                subprocess.run([
                    'notify-send',
                    '-a', 'Whisper Toggle',
                    '-i', icon,
                    title,
                    message
                ], check=False)
            except:
                pass