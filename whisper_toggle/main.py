#!/usr/bin/env python3
"""
Whisper Toggle - Real-time voice transcription with hardware toggle

A privacy-focused voice transcription tool that runs locally and provides
real-time speech-to-text conversion with hardware button toggle support.

Features:
- Hardware toggle button support (Keychron X button / F16 key)
- Real-time transcription using OpenAI Whisper
- Smart visual and audio indicators
- Automatic text typing via ydotool
- System service integration
- GNOME/Wayland compatibility

Author: Claude Code Assistant & User
License: MIT
"""

import pyaudio
import numpy as np
from faster_whisper import WhisperModel
import threading
import queue
import time
import sys
import subprocess
import evdev
import select
from scipy import signal
import warnings
import os

# Suppress ALSA and other warnings for cleaner output
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings("ignore")

class SmartIndicator:
    """
    Handles visual and audio feedback for recording state.
    
    Provides multiple indicator methods:
    - GNOME notifications with persistent display
    - System audio feedback (beeps)
    - Desktop status file as backup
    """
    
    def __init__(self):
        self.is_showing = False
        self.notification_id = None
        self.last_activity_time = 0
        
    def update_status_file(self, is_recording):
        """Update desktop status file as backup indicator"""
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            status_file = os.path.join(desktop_path, "🎤 Whisper Status.txt")
            
            if is_recording:
                content = """🔴 WHISPER RECORDING

Microphone is ON
Press X button to stop

Status: Listening for speech...
"""
            else:
                content = """⚪ WHISPER OFF

Microphone is OFF  
Press X button to start

Status: Ready to record
"""
            
            with open(status_file, 'w') as f:
                f.write(content)
        except:
            pass
        
    def play_sound(self, sound_name):
        """Play system sound"""
        try:
            # Try different sound methods
            subprocess.run(['paplay', f'/usr/share/sounds/Oxygen-Sys-App-{sound_name}.ogg'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            try:
                subprocess.run(['play', '-q', f'/usr/share/sounds/alsa/{sound_name}.wav'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                # Fallback to simple beep
                subprocess.run(['speaker-test', '-t', 'sine', '-f', '800', '-l', '1'], 
                             timeout=0.1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    def show_indicator(self):
        """Show recording indicator"""
        if self.is_showing:
            return
            
        self.is_showing = True
        
        # Update status file
        self.update_status_file(True)
        
        # Play start sound
        self.play_sound('positive')
        
        # Show persistent notification
        try:
            result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest=org.freedesktop.Notifications',
                '--object-path=/org/freedesktop/Notifications', 
                '--method=org.freedesktop.Notifications.Notify',
                'Whisper',  # app name
                '0',        # notification id (0 = new)
                'audio-input-microphone',  # icon
                '🎤 Whisper Recording',  # summary
                'Microphone is ON - Press X to stop\nReady to transcribe speech',  # body
                '[]',       # actions
                '{"urgency": <byte 2>, "resident": <true>}',  # hints (critical + persistent)
                '0'         # timeout (0 = persistent)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract notification ID from response
                output = result.stdout.strip()
                if output.startswith('(uint32 '):
                    self.notification_id = output.split(' ')[1].rstrip(',)')
                    print(f"🎤 Recording indicator shown (ID: {self.notification_id})")
        except Exception as e:
            print(f"Notification failed: {e}")
            
    def hide_indicator(self):
        """Hide recording indicator"""
        if not self.is_showing:
            return
            
        self.is_showing = False
        
        # Update status file
        self.update_status_file(False)
        
        # Play stop sound
        self.play_sound('negative')
        
        # Close persistent notification if we have an ID
        if self.notification_id:
            try:
                subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest=org.freedesktop.Notifications',
                    '--object-path=/org/freedesktop/Notifications',
                    '--method=org.freedesktop.Notifications.CloseNotification',
                    self.notification_id
                ], capture_output=True)
                print(f"🎤 Closed recording notification")
            except:
                pass
            self.notification_id = None
            
        # Show brief "stopped" notification
        try:
            subprocess.run([
                'gdbus', 'call', '--session',
                '--dest=org.freedesktop.Notifications',
                '--object-path=/org/freedesktop/Notifications',
                '--method=org.freedesktop.Notifications.Notify',
                'Whisper', '0', 'audio-input-microphone',
                '🎤 Whisper Stopped', 'Microphone is OFF',
                '[]', '{"urgency": <byte 1>}', '2000'  # 2 second timeout
            ], capture_output=True)
        except:
            pass
            
    def update_activity(self, level):
        """Update indicator with activity level"""
        if not self.is_showing or not self.notification_id:
            return
            
        current_time = time.time()
        
        # Only update notification every 500ms to avoid spam
        if current_time - self.last_activity_time < 0.5:
            return
            
        self.last_activity_time = current_time
        
        if level > 0.01:
            # Show activity in notification
            bars = '▸' * min(int(level * 10), 8)
            try:
                subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest=org.freedesktop.Notifications',
                    '--object-path=/org/freedesktop/Notifications',
                    '--method=org.freedesktop.Notifications.Notify',
                    'Whisper', self.notification_id,
                    'audio-input-microphone',
                    f'🎤 Recording {bars}',
                    'Speaking detected - processing audio',
                    '[]', '{"urgency": <byte 2>, "resident": <true>}', '0'
                ], capture_output=True)
            except:
                pass

class ToggleTranscriber:
    def __init__(self, silence_threshold=8, model_size="base", device_index=3):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.silence_threshold = silence_threshold
        self.silence_counter = 0
        self.whisper_sample_rate = 16000
        self.chunk_size = 4096
        self.running = True
        
        # Smart indicator
        self.indicator = SmartIndicator()
        
        # Find Keychron keyboard
        self.setup_keychron_device()
        
        # Audio setup - suppress PyAudio output
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(2)
        os.dup2(devnull, 2)
        
        self.audio = pyaudio.PyAudio()
        
        # Get device info
        device_info = self.audio.get_device_info_by_index(device_index)
        self.device_sample_rate = int(device_info['defaultSampleRate'])
        
        # Open stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.device_sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )
        
        # Restore stderr
        os.dup2(old_stderr, 2)
        os.close(devnull)
        
        print(f"🎤 Whisper Toggle with Smart Indicators")
        print(f"Device: {device_info['name']}")
        print(f"Press X button (F16) to toggle ON/OFF")
        print(f"Press Ctrl+C to quit")
        print(f"\nStatus: OFF (waiting for X button)")
        
    def setup_keychron_device(self):
        """Find Keychron keyboard device"""
        self.keyboard = None
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        
        for device in devices:
            if 'keychron' in device.name.lower() and 'keyboard' in device.name.lower():
                self.keyboard = device
                break
        
        if not self.keyboard:
            print("Warning: Keychron keyboard not found - toggle disabled")
            
    def monitor_keys(self):
        """Monitor for F16 key"""
        if not self.keyboard:
            return
            
        while self.running:
            try:
                r, w, x = select.select([self.keyboard], [], [], 0.1)
                
                if r:
                    for event in self.keyboard.read():
                        if event.type == evdev.ecodes.EV_KEY and event.code == 186 and event.value == 1:
                            self.toggle_listening()
                                    
            except Exception:
                pass
                    
    def toggle_listening(self):
        """Toggle listening state"""
        self.is_listening = not self.is_listening
        status = "ON" if self.is_listening else "OFF"
        print(f"Status: {status}")
        
        # Update smart indicator
        if self.is_listening:
            self.indicator.show_indicator()
            self.silence_counter = 0
            while not self.audio_queue.empty():
                self.audio_queue.get()
        else:
            self.indicator.hide_indicator()
    
    def resample_audio(self, audio_data, orig_sr, target_sr):
        """Resample audio"""
        if orig_sr == target_sr:
            return audio_data
        
        number_of_samples = int(len(audio_data) * target_sr / orig_sr)
        resampled = signal.resample(audio_data, number_of_samples)
        
        return resampled
        
    def audio_callback(self):
        """Capture audio"""
        while self.running:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                
                if self.is_listening:
                    audio_level = np.max(np.abs(audio_data))
                    if audio_level < 0.002:
                        self.silence_counter += 1
                    else:
                        self.silence_counter = 0
                        # Update smart indicator with activity
                        self.indicator.update_activity(audio_level)
                        
                        # Show activity in terminal too
                        bars = min(int(audio_level * 500), 10)
                        print(f"\r{'▸' * bars}", end='', flush=True)
                    
                    # Resample to 16kHz
                    if self.device_sample_rate != self.whisper_sample_rate:
                        audio_data = self.resample_audio(audio_data, self.device_sample_rate, self.whisper_sample_rate)
                    
                    self.audio_queue.put(audio_data)
                    
            except Exception:
                break
                
    def transcribe_worker(self):
        """Transcribe audio"""
        audio_buffer = []
        
        while self.running:
            try:
                if not self.audio_queue.empty() and self.is_listening:
                    chunk = self.audio_queue.get()
                    audio_buffer.extend(chunk)
                    
                    min_buffer_size = int(self.whisper_sample_rate * 0.75)
                    
                    if len(audio_buffer) > min_buffer_size and self.silence_counter >= self.silence_threshold:
                        audio_np = np.array(audio_buffer, dtype=np.float32)
                        
                        max_vol = np.max(np.abs(audio_np))
                        
                        if max_vol > 0.002:
                            # Transcribe
                            segments, _ = self.model.transcribe(audio_np, language="en")
                            text = " ".join([segment.text.strip() for segment in segments])
                            
                            if text and len(text.strip()) > 1:
                                print(f"\r✓ {text}")
                                # Type the text with ydotool
                                time.sleep(0.05)
                                subprocess.run(['ydotool', 'type', text], 
                                             stdout=subprocess.DEVNULL, 
                                             stderr=subprocess.DEVNULL)
                                
                                # Show transcription in notification
                                if self.notification_id:
                                    try:
                                        subprocess.run([
                                            'gdbus', 'call', '--session',
                                            '--dest=org.freedesktop.Notifications',
                                            '--object-path=/org/freedesktop/Notifications',
                                            '--method=org.freedesktop.Notifications.Notify',
                                            'Whisper', self.indicator.notification_id,
                                            'audio-input-microphone',
                                            '🎤 Recording',
                                            f'Transcribed: "{text}"',
                                            '[]', '{"urgency": <byte 2>, "resident": <true>}', '0'
                                        ], capture_output=True)
                                    except:
                                        pass
                                
                                # Restore status
                                status = "ON" if self.is_listening else "OFF"
                                print(f"Status: {status}", end='', flush=True)
                            
                        audio_buffer = []
                        self.silence_counter = 0
                        
                    elif len(audio_buffer) > self.whisper_sample_rate * 30:
                        audio_buffer = audio_buffer[self.whisper_sample_rate * 10:]
                        
                else:
                    time.sleep(0.01)
                    
            except Exception:
                time.sleep(0.1)
                
    def run(self):
        """Main loop"""
        audio_thread = threading.Thread(target=self.audio_callback, daemon=True)
        transcribe_thread = threading.Thread(target=self.transcribe_worker, daemon=True)
        key_thread = threading.Thread(target=self.monitor_keys, daemon=True)
        
        audio_thread.start()
        transcribe_thread.start()
        key_thread.start()
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n")
            self.running = False
            
        self.cleanup()
            
    def cleanup(self):
        """Clean up"""
        self.running = False
        self.indicator.hide_indicator()
        time.sleep(0.1)
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

if __name__ == "__main__":
    silence_threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    device_index = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    try:
        transcriber = ToggleTranscriber(silence_threshold=silence_threshold, device_index=device_index)
        transcriber.run()
    except Exception as e:
        print(f"Error: {e}")