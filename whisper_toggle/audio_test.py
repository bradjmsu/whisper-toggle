"""
Audio device testing functionality for Whisper Toggle.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import threading
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

# Try to import pyaudio
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    logger.warning("PyAudio not available - audio testing disabled")


class AudioTestDialog(Gtk.Dialog):
    """Dialog for testing audio input devices."""
    
    def __init__(self, parent, device_index=None):
        super().__init__(
            title="Microphone Test",
            transient_for=parent,
            flags=0
        )
        self.device_index = device_index
        self.testing = False
        self.stream = None
        self.p = None
        
        self.set_default_size(400, 300)
        
        # Get content area
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)
        
        # Device info label
        self.info_label = Gtk.Label()
        box.pack_start(self.info_label, False, False, 0)
        
        # Level meter frame
        meter_frame = Gtk.Frame(label="Audio Level")
        box.pack_start(meter_frame, True, True, 0)
        
        meter_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        meter_box.set_border_width(10)
        meter_frame.add(meter_box)
        
        # Peak level bar
        self.peak_bar = Gtk.ProgressBar()
        self.peak_bar.set_show_text(True)
        meter_box.pack_start(Gtk.Label(label="Peak Level:"), False, False, 0)
        meter_box.pack_start(self.peak_bar, False, False, 0)
        
        # RMS level bar
        self.rms_bar = Gtk.ProgressBar()
        self.rms_bar.set_show_text(True)
        meter_box.pack_start(Gtk.Label(label="Average Level:"), False, False, 0)
        meter_box.pack_start(self.rms_bar, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="Click 'Start Test' to begin")
        box.pack_start(self.status_label, False, False, 0)
        
        # Add buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        self.test_button = self.add_button("Start Test", Gtk.ResponseType.OK)
        
        # Connect signals
        self.connect("response", self.on_response)
        
        # Update device info
        self.update_device_info()
        
        self.show_all()
    
    def update_device_info(self):
        """Update device information label."""
        if not HAS_PYAUDIO:
            self.info_label.set_text("PyAudio not installed - cannot test audio")
            self.test_button.set_sensitive(False)
            return
        
        try:
            p = pyaudio.PyAudio()
            if self.device_index is None:
                # Use default device
                info = p.get_default_input_device_info()
                self.device_index = info['index']
            else:
                info = p.get_device_info_by_index(self.device_index)
            
            text = f"<b>Device:</b> {info['name']}\n"
            text += f"<b>Channels:</b> {info['maxInputChannels']}\n"
            text += f"<b>Sample Rate:</b> {int(info['defaultSampleRate'])} Hz"
            self.info_label.set_markup(text)
            
            p.terminate()
        except Exception as e:
            self.info_label.set_text(f"Error: {str(e)}")
            self.test_button.set_sensitive(False)
    
    def on_response(self, dialog, response_id):
        """Handle dialog response."""
        if response_id == Gtk.ResponseType.OK:
            if self.testing:
                self.stop_test()
            else:
                self.start_test()
        else:
            self.stop_test()
            self.destroy()
    
    def start_test(self):
        """Start audio testing."""
        if not HAS_PYAUDIO:
            return
        
        self.testing = True
        self.test_button.set_label("Stop Test")
        self.status_label.set_text("Testing... Speak into your microphone")
        
        # Start audio thread
        self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.audio_thread.start()
    
    def stop_test(self):
        """Stop audio testing."""
        self.testing = False
        self.test_button.set_label("Start Test")
        self.status_label.set_text("Test stopped")
        
        # Reset meters
        GLib.idle_add(self.update_meters, 0.0, 0.0)
    
    def audio_worker(self):
        """Audio processing thread."""
        try:
            self.p = pyaudio.PyAudio()
            
            # Get device info
            info = self.p.get_device_info_by_index(self.device_index)
            rate = int(info['defaultSampleRate'])
            channels = min(info['maxInputChannels'], 2)  # Use max 2 channels
            
            # Open stream
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024
            )
            
            while self.testing:
                try:
                    # Read audio data
                    data = self.stream.read(1024, exception_on_overflow=False)
                    
                    # Convert to numpy array
                    audio = np.frombuffer(data, dtype=np.int16)
                    
                    # Calculate levels
                    if len(audio) > 0:
                        # Normalize to 0-1 range
                        audio_float = audio.astype(float) / 32768.0
                        
                        # Calculate RMS (average level)
                        rms = np.sqrt(np.mean(audio_float**2))
                        
                        # Calculate peak
                        peak = np.max(np.abs(audio_float))
                        
                        # Update UI
                        GLib.idle_add(self.update_meters, peak, rms)
                
                except Exception as e:
                    logger.error(f"Audio read error: {e}")
                    break
            
        except Exception as e:
            GLib.idle_add(self.show_error, str(e))
        finally:
            # Cleanup
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
    
    def update_meters(self, peak, rms):
        """Update level meters in UI."""
        # Update peak meter
        self.peak_bar.set_fraction(min(peak, 1.0))
        self.peak_bar.set_text(f"{int(peak * 100)}%")
        
        # Update RMS meter
        self.rms_bar.set_fraction(min(rms, 1.0))
        self.rms_bar.set_text(f"{int(rms * 100)}%")
        
        # Color code based on level
        if peak > 0.9:
            # Red - clipping
            self.peak_bar.set_name("level-high")
        elif peak > 0.7:
            # Yellow - good
            self.peak_bar.set_name("level-medium")
        else:
            # Green - low
            self.peak_bar.set_name("level-low")
    
    def show_error(self, error_msg):
        """Show error message."""
        self.status_label.set_markup(f"<span color='red'>Error: {error_msg}</span>")
        self.test_button.set_sensitive(False)


def get_audio_devices():
    """Get list of available audio input devices."""
    devices = []
    
    if not HAS_PYAUDIO:
        return devices
    
    try:
        p = pyaudio.PyAudio()
        
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                # Format device name
                name = info['name']
                host_api = p.get_host_api_info_by_index(info['hostApi'])['name']
                
                # Clean up ALSA device names
                if '(' in name and ')' in name:
                    name = name.split('(')[0].strip()
                
                devices.append({
                    'index': i,
                    'name': name,
                    'host_api': host_api,
                    'channels': info['maxInputChannels'],
                    'rate': int(info['defaultSampleRate'])
                })
        
        p.terminate()
    except Exception as e:
        logger.error(f"Failed to enumerate audio devices: {e}")
    
    return devices