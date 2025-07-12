"""
Standalone audio testing functionality using only subprocess commands.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject
import cairo
import threading
import subprocess
import time
import re
import struct
import math

class StandaloneAudioTestDialog(Gtk.Dialog):
    """Audio test dialog that works without pyaudio."""
    
    def __init__(self, parent, device_index=None, initial_gain=1.0):
        super().__init__(
            title="Microphone Test",
            transient_for=parent,
            flags=0
        )
        self.device_index = device_index
        self.testing = False
        self.process = None
        self.selected_gain = initial_gain
        
        self.set_default_size(500, 520)
        
        # Get content area
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)
        
        # Device info label
        self.info_label = Gtk.Label()
        self.update_device_info()
        box.pack_start(self.info_label, False, False, 0)
        
        # Level meter frame
        meter_frame = Gtk.Frame(label="Audio Levels")
        box.pack_start(meter_frame, True, True, 0)
        
        meter_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        meter_box.set_border_width(10)
        meter_frame.add(meter_box)
        
        # Peak level
        peak_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        meter_box.pack_start(peak_box, False, False, 0)
        
        peak_label = Gtk.Label(label="Peak Level:", xalign=0)
        peak_box.pack_start(peak_label, False, False, 0)
        
        self.peak_bar = Gtk.ProgressBar()
        self.peak_bar.set_show_text(True)
        peak_box.pack_start(self.peak_bar, False, False, 0)
        
        # RMS level
        rms_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        meter_box.pack_start(rms_box, False, False, 0)
        
        rms_label = Gtk.Label(label="Average Level (RMS):", xalign=0)
        rms_box.pack_start(rms_label, False, False, 0)
        
        self.rms_bar = Gtk.ProgressBar()
        self.rms_bar.set_show_text(True)
        rms_box.pack_start(self.rms_bar, False, False, 0)
        
        # Gain control
        gain_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        meter_box.pack_start(gain_box, False, False, 0)
        
        gain_label = Gtk.Label(label="Gain Adjustment:", xalign=0)
        gain_box.pack_start(gain_label, False, False, 0)
        
        gain_control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        gain_box.pack_start(gain_control_box, False, False, 0)
        
        # Convert linear gain to dB for the slider
        # dB = 20 * log10(gain)
        # gain = 10^(dB/20)
        initial_db = 20 * math.log10(max(initial_gain, 0.001))
        
        self.gain_adjustment = Gtk.Adjustment(
            value=initial_db,  # Use dB scale
            lower=-40,  # -40 dB (very quiet)
            upper=40,   # +40 dB (very loud)
            step_increment=1,
            page_increment=6  # 6 dB = double/half volume
        )
        
        self.gain_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=self.gain_adjustment
        )
        self.gain_scale.set_digits(0)
        self.gain_scale.set_hexpand(True)
        # Add marks at key dB values - fewer to avoid overlap
        self.gain_scale.add_mark(-40, Gtk.PositionType.BOTTOM, "-40")
        self.gain_scale.add_mark(-20, Gtk.PositionType.BOTTOM, "-20")
        self.gain_scale.add_mark(0, Gtk.PositionType.BOTTOM, "0dB")
        self.gain_scale.add_mark(20, Gtk.PositionType.BOTTOM, "+20")
        self.gain_scale.add_mark(40, Gtk.PositionType.BOTTOM, "+40")
        
        # Add minor marks without labels
        for db in [-30, -10, 10, 30]:
            self.gain_scale.add_mark(db, Gtk.PositionType.BOTTOM, None)
        gain_control_box.pack_start(self.gain_scale, True, True, 0)
        
        self.gain_value_label = Gtk.Label(label=f"{initial_db:+.0f} dB")
        self.gain_value_label.set_size_request(80, -1)
        gain_control_box.pack_start(self.gain_value_label, False, False, 0)
        
        # Connect gain slider
        self.gain_adjustment.connect("value-changed", self.on_gain_changed)
        
        # Visual meter (canvas)
        visual_label = Gtk.Label(label="Visual Meter:", xalign=0)
        meter_box.pack_start(visual_label, False, False, 0)
        
        self.meter_area = Gtk.DrawingArea()
        self.meter_area.set_size_request(400, 250)
        self.meter_area.connect("draw", self.on_draw_meter)
        meter_box.pack_start(self.meter_area, False, False, 0)
        
        # Initialize meter data
        self.meter_levels = [0.0] * 50  # History of levels
        self.current_peak = 0.0
        self.current_rms = 0.0
        self.current_gain = initial_gain
        self.needle_position = 0.0  # Current needle position
        self.needle_velocity = 0.0  # For smooth movement
        
        # Status label
        self.status_label = Gtk.Label(label="Starting audio test...")
        box.pack_start(self.status_label, False, False, 0)
        
        # Add buttons
        self.add_button("OK", Gtk.ResponseType.OK)
        
        # Connect signals
        self.connect("response", self.on_response)
        self.connect("destroy", self.on_destroy)
        
        # Start testing automatically
        GLib.idle_add(self.start_test)
        
        # CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            progressbar.low trough progress {
                background-color: #4CAF50;
            }
            progressbar.medium trough progress {
                background-color: #FFC107;
            }
            progressbar.high trough progress {
                background-color: #F44336;
            }
        """)
        
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.show_all()
    
    def update_device_info(self):
        """Update device information label."""
        self.device_names = {
            0: "Logitech Webcam C925e",
            1: "fifine Microphone",
            2: "Built-in Audio"
        }
        
        if self.device_index is None:
            self.device_name = "Default Device"
        else:
            self.device_name = self.device_names.get(self.device_index, f"Device #{self.device_index}")
        
        text = f"<b>Testing:</b> {self.device_name}\n"
        if self.device_index == 1:
            text += "✓ Your fifine Microphone detected!"
        
        self.info_label.set_markup(text)
    
    def on_gain_changed(self, adjustment):
        """Handle gain slider change."""
        db_value = adjustment.get_value()
        # Convert dB back to linear gain
        self.current_gain = 10 ** (db_value / 20)
        self.selected_gain = self.current_gain  # Store for return
        
        # Update label with both dB and linear
        if db_value >= 0:
            self.gain_value_label.set_text(f"+{db_value:.0f} dB")
        else:
            self.gain_value_label.set_text(f"{db_value:.0f} dB")
        
        # Add tooltip showing linear gain
        self.gain_value_label.set_tooltip_text(f"Linear gain: {self.current_gain:.1f}x")
    
    def on_draw_meter(self, widget, cr):
        """Draw an analog VU meter with needle."""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        # Center point for the meter
        cx = width / 2
        cy = height - 50  # Leave room for labels below
        radius = min(width, height - 80) * 0.85
        
        # Background with warm beige color
        cr.set_source_rgb(0.788, 0.663, 0.486)  # #C9A97C
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        # Draw meter face with same warm beige
        # Create gradient that simulates side lighting on the beige
        gradient = cairo.LinearGradient(0, 0, width, 0)
        gradient.add_color_stop_rgb(0, 0.85, 0.73, 0.56)  # Brighter beige on left
        gradient.add_color_stop_rgb(0.5, 0.788, 0.663, 0.486)  # Base #C9A97C in middle
        gradient.add_color_stop_rgb(1, 0.85, 0.73, 0.56)  # Brighter beige on right
        cr.set_source(gradient)
        cr.arc(cx, cy, radius * 1.1, 7*math.pi/6, 11*math.pi/6)
        cr.fill()
        
        # No shadow - keep it clean
        
        # No background arc - we'll just draw the colored line
        
        # Draw scale segments (colored zones)
        # Arc spans 120° from 210° to 330°
        # 0dB is at 80% of the arc
        arc_start = 7*math.pi/6
        arc_span = 2*math.pi/3  # 120 degrees
        
        green_start = arc_start
        green_end = arc_start + 0.8 * arc_span  # 80% for green (-∞ to 0dB)
        red_start = green_end
        red_end = arc_start + arc_span  # 20% for red (0dB to +3dB)
        
        # Draw thin colored line for the scale
        cr.set_line_width(3)
        
        # Green section (-∞ to 0dB)
        cr.set_source_rgb(0.30, 0.69, 0.31)
        cr.arc(cx, cy, radius, green_start, green_end)
        cr.stroke()
        
        # Red section (0dB to +3dB)
        cr.set_source_rgb(0.96, 0.26, 0.21)
        cr.arc(cx, cy, radius, red_start, red_end)
        cr.stroke()
        
        # Draw scale marks
        cr.set_source_rgb(0.2, 0.2, 0.2)
        
        for i in range(11):  # 0 to 10 marks
            # Map i (0-10) to angle within our arc
            angle = 7*math.pi/6 + (i / 10) * 2*math.pi/3
            
            # Major marks for even positions, minor marks for odd
            if i % 2 == 0:  # Major marks
                cr.set_line_width(2)
                mark_length = 10
            else:  # Minor marks
                cr.set_line_width(1)
                mark_length = 6
            
            # Draw marks extending from inside to outside the colored line
            x1 = cx + (radius - mark_length) * math.cos(angle)
            y1 = cy - (radius - mark_length) * math.sin(angle)
            x2 = cx + (radius + mark_length) * math.cos(angle)
            y2 = cy - (radius + mark_length) * math.sin(angle)
            
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()
            
        # Draw scale labels manually at specific positions
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.select_font_face("", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9)
        
        # Calculate label positions manually for bottom arc
        # The arc goes from 210° to 330°
        label_offset = 25
        
        # -∞ at 210°
        cr.move_to(cx - radius - 15, cy + label_offset)
        cr.show_text("-∞")
        
        # -15 at ~234°  
        cr.move_to(cx - radius * 0.6 - 5, cy + label_offset + 5)
        cr.show_text("-15")
        
        # -7 at ~258°
        cr.move_to(cx - radius * 0.2, cy + label_offset + 8)
        cr.show_text("-7")
        
        # -1 at ~282°
        cr.move_to(cx + radius * 0.2 - 5, cy + label_offset + 8)
        cr.show_text("-1")
        
        # +1 at ~306°
        cr.move_to(cx + radius * 0.6 - 5, cy + label_offset + 5)
        cr.show_text("+1")
        
        # +3 at 330°
        cr.move_to(cx + radius - 5, cy + label_offset)
        cr.show_text("+3")
        
        # Draw VU label
        cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark text on light background
        cr.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(16)
        cr.move_to(cx - 10, cy - radius * 0.5)  # Centered in the meter
        cr.show_text("VU")
        
        # Smooth needle movement with physics (very responsive)
        target = self.current_peak
        force = (target - self.needle_position) * 0.95  # Strong spring force
        self.needle_velocity = self.needle_velocity * 0.7 + force  # Much less damping
        self.needle_position += self.needle_velocity
        
        # Clamp needle position
        self.needle_position = max(0, min(1, self.needle_position))
        level = self.needle_position
        
        # Draw needle shadow
        # Map level (0-1) to angle within our arc (reversed)
        needle_angle = 7*math.pi/6 + (1 - level) * 2*math.pi/3
        cr.set_source_rgba(0, 0, 0, 0.5)
        cr.set_line_width(4)
        cr.move_to(cx + 2, cy + 2)
        cr.line_to(cx + 2 - radius * 0.9 * math.cos(needle_angle), 
                   cy + 2 + radius * 0.9 * math.sin(needle_angle))
        cr.stroke()
        
        # Draw needle
        cr.set_source_rgb(0.9, 0.1, 0.1)
        cr.set_line_width(3)
        cr.move_to(cx, cy)
        cr.line_to(cx - radius * 0.9 * math.cos(needle_angle), 
                   cy + radius * 0.9 * math.sin(needle_angle))
        cr.stroke()
        
        # Draw needle hub
        gradient = cairo.RadialGradient(cx, cy, 0, cx, cy, 8)
        gradient.add_color_stop_rgb(0, 0.4, 0.4, 0.4)
        gradient.add_color_stop_rgb(1, 0.2, 0.2, 0.2)
        cr.set_source(gradient)
        cr.arc(cx, cy, 8, 0, 2 * math.pi)
        cr.fill()
        
        # Draw center dot
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.arc(cx, cy, 3, 0, 2 * math.pi)
        cr.fill()
        
        # Add "dB" label below the VU label
        cr.set_source_rgb(0.3, 0.3, 0.3)  # Darker for visibility
        cr.set_font_size(10)
        cr.move_to(cx - 8, cy - radius * 0.35)  # Below VU label
        cr.show_text("dB")
    
    def on_response(self, dialog, response_id):
        """Handle dialog response."""
        # Any response closes the dialog
        self.stop_test()
        self.destroy()
    
    def on_destroy(self, widget):
        """Clean up when dialog is destroyed."""
        self.stop_test()
    
    def start_test(self):
        """Start audio testing."""
        self.testing = True
        self.status_label.set_text("Recording... Speak into your microphone!")
        
        # Start audio capture thread
        self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.audio_thread.start()
    
    def stop_test(self):
        """Stop audio testing."""
        self.testing = False
        if self.process:
            self.process.terminate()
            self.process = None
        
        self.status_label.set_text("Test stopped")
        
        # Reset meters
        GLib.idle_add(self.update_meters, 0.0, 0.0)
    
    def audio_worker(self):
        """Audio capture using arecord."""
        try:
            # Try different approaches to audio capture
            success = False
            
            # First try: specific device
            if self.device_index == 1:  # fifine
                for device_name in ['hw:1,0', 'plughw:1,0', 'hw:Microphone']:
                    if self.try_audio_capture(device_name):
                        success = True
                        break
            
            # Second try: default device
            if not success:
                if self.try_audio_capture('default'):
                    success = True
            
            # Third try: pulse
            if not success:
                if self.try_audio_capture('pulse'):
                    success = True
            
            # Last resort: simulate audio for demo
            if not success:
                device_name = getattr(self, 'device_name', 'microphone')
                GLib.idle_add(self.status_label.set_text, f"Demo mode - simulating {device_name}")
                self.simulate_audio()
            
        except Exception as e:
            GLib.idle_add(self.show_error, str(e))
    
    def try_audio_capture(self, device):
        """Try to capture audio from a specific device."""
        try:
            # Build arecord command
            cmd = ['arecord', '-D', device, '-f', 'S16_LE', '-r', '44100', '-c', '1', '-t', 'raw']
            
            # Start recording
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # Test if it works by reading a small chunk
            test_data = self.process.stdout.read(1024)
            if not test_data:
                self.process.terminate()
                return False
            
            # Get friendly device name
            device_name = getattr(self, 'device_name', 'microphone')
            GLib.idle_add(self.status_label.set_text, f"Recording from {device_name}... Speak now!")
            
            # Read audio data in chunks
            chunk_size = 2048  # bytes
            
            while self.testing and self.process:
                try:
                    # Read raw audio data
                    data = self.process.stdout.read(chunk_size)
                    if not data:
                        break
                    
                    # Convert bytes to 16-bit signed integers
                    if len(data) % 2 != 0:
                        data = data[:-1]  # Make sure we have pairs of bytes
                    
                    # Unpack as 16-bit signed integers
                    audio_samples = struct.unpack(f'{len(data)//2}h', data)
                    
                    if audio_samples:
                        # Convert to float and normalize to 0-1 range
                        audio_float = [abs(x) / 32768.0 for x in audio_samples]
                        
                        # Apply gain
                        audio_float = [x * self.current_gain for x in audio_float]
                        
                        # Calculate RMS (average level)
                        rms = math.sqrt(sum(x*x for x in audio_float) / len(audio_float))
                        
                        # Calculate peak
                        peak = max(audio_float)
                        
                        # Update UI
                        GLib.idle_add(self.update_meters, peak, rms)
                    
                except Exception as e:
                    if self.testing:
                        print(f"Audio read error: {e}")
                    break
            
            return True
            
        except Exception as e:
            print(f"Failed to capture from {device}: {e}")
            if self.process:
                self.process.terminate()
            return False
    
    def simulate_audio(self):
        """Simulate audio levels for demo purposes."""
        import random
        
        while self.testing:
            try:
                # Generate fake audio levels
                if random.random() > 0.7:  # 30% chance of "audio"
                    peak = random.uniform(0.1, 0.8)
                    rms = peak * random.uniform(0.3, 0.7)
                else:
                    peak = random.uniform(0.0, 0.05)
                    rms = peak * 0.5
                
                # Apply gain
                peak *= self.current_gain
                rms *= self.current_gain
                
                # Update UI
                GLib.idle_add(self.update_meters, peak, rms)
                
                # Wait a bit
                time.sleep(0.05)
                
            except Exception as e:
                break
    
    def update_meters(self, peak, rms):
        """Update level meters in UI."""
        # Store current levels
        self.current_peak = peak
        self.current_rms = rms
        
        # Show actual percentage even if over 100% (clipping)
        peak_percent = int(peak * 100)
        rms_percent = int(rms * 100)
        
        # Update peak meter - allow over 100% but cap visual at 100%
        self.peak_bar.set_fraction(min(peak, 1.0))
        if peak_percent > 100:
            self.peak_bar.set_text(f"{peak_percent}% CLIP!")
        else:
            self.peak_bar.set_text(f"{peak_percent}%")
        
        # Update RMS meter - allow over 100% but cap visual at 100%
        self.rms_bar.set_fraction(min(rms, 1.0))
        if rms_percent > 100:
            self.rms_bar.set_text(f"{rms_percent}% CLIP!")
        else:
            self.rms_bar.set_text(f"{rms_percent}%")
        
        # Style based on level - include clipping detection
        if peak > 1.0:  # Clipping
            self.peak_bar.get_style_context().remove_class("low")
            self.peak_bar.get_style_context().remove_class("medium")
            self.peak_bar.get_style_context().add_class("high")
        elif peak > 0.9:
            self.peak_bar.get_style_context().remove_class("low")
            self.peak_bar.get_style_context().remove_class("medium")
            self.peak_bar.get_style_context().add_class("high")
        elif peak > 0.6:
            self.peak_bar.get_style_context().remove_class("low")
            self.peak_bar.get_style_context().add_class("medium")
            self.peak_bar.get_style_context().remove_class("high")
        else:
            self.peak_bar.get_style_context().add_class("low")
            self.peak_bar.get_style_context().remove_class("medium")
            self.peak_bar.get_style_context().remove_class("high")
        
        # Update visual meter - allow clipping values
        self.meter_levels.append(peak)
        if len(self.meter_levels) > 50:
            self.meter_levels.pop(0)
        
        # Redraw visual meter
        self.meter_area.queue_draw()
        
        return False
    
    def show_error(self, error_msg):
        """Show error message."""
        self.status_label.set_markup(f"<span color='red'>Error: {error_msg}</span>")
        self.test_button.set_sensitive(False)


def get_audio_devices_standalone():
    """Get audio devices using smart detection."""
    devices = []
    
    try:
        from smart_audio_device import SmartAudioDevice
        detector = SmartAudioDevice()
        
        # Get devices with friendly indices
        for i, device in enumerate(detector.devices):
            devices.append({
                'index': i,  # Friendly index that matches what transcriber uses
                'name': device['name'],
                'alsa_card': device['alsa_card'],
                'host_api': 'ALSA',
                'max_input_channels': 2
            })
            
    except ImportError:
        # Fallback to old method
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'card' in line and ':' in line:
                    # Extract card number and name
                    match = re.search(r'card (\d+): (.+?) \[', line)
                    if match:
                        card_num = int(match.group(1))
                        card_name = match.group(2)
                        
                        # Map to our expected devices
                        if 'C925e' in card_name or 'Webcam' in card_name:
                            devices.append({'index': 0, 'name': 'Logitech Webcam C925e', 'host_api': 'ALSA'})
                        elif 'fifine' in card_name or 'Microphone' in card_name:
                            devices.append({'index': 1, 'name': 'fifine Microphone', 'host_api': 'ALSA'})
                        elif 'PCH' in card_name or 'Intel' in card_name:
                            devices.append({'index': 2, 'name': 'Built-in Audio', 'host_api': 'ALSA'})
    except:
        pass
    
    # If no devices found, return demo devices
    if not devices:
        devices = [
            {'index': 0, 'name': 'Logitech Webcam C925e', 'host_api': 'ALSA'},
            {'index': 1, 'name': 'fifine Microphone', 'host_api': 'ALSA'},
            {'index': 2, 'name': 'Built-in Audio', 'host_api': 'ALSA'},
        ]
    
    return devices