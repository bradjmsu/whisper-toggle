#!/usr/bin/env python3
"""
Simple transcription module that works without sudo.
"""

import subprocess
import threading
import queue
import time
import os
import tempfile
import wave
import struct

class SimpleTranscriber:
    """Simple transcriber using command-line tools."""
    
    def __init__(self, config):
        self.config = config
        self.recording = False
        self.audio_data = []
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.actual_sample_rate = None
        self.actual_channels = None
        
    def start_recording(self):
        """Start recording audio using smart device detection."""
        self.recording = True
        self.audio_data = []
        
        def record_thread():
            try:
                # Use smart device detection
                from smart_audio_device import SmartAudioDevice
                detector = SmartAudioDevice()
                
                device_id = self.config.get('audio_device')
                device_string = None
                
                if device_id is not None:
                    # Get the correct device string
                    device_string = detector.get_device_string(device_id)
                    print(f"Smart device mapping: {device_id} -> {device_string}")
                else:
                    # Auto-detect best device
                    best_device = detector.get_best_device()
                    if best_device:
                        device_string = best_device['device_string']
                        print(f"Auto-detected device: {best_device['name']} ({device_string})")
                
                # List of configurations to try
                configs = []
                
                if device_string:
                    # Try with the smart device string
                    configs.extend([
                        # Stereo first (most common for USB mics)
                        ['arecord', '-f', 'S16_LE', '-r', '44100', '-c', '2', '-D', device_string],
                        ['arecord', '-f', 'S16_LE', '-r', '48000', '-c', '2', '-D', device_string],
                        # Try mono (some mics are mono only)
                        ['arecord', '-f', 'S16_LE', '-r', '44100', '-c', '1', '-D', device_string],
                        ['arecord', '-f', 'S16_LE', '-r', '16000', '-c', '1', '-D', device_string],
                    ])
                
                # Always add default as fallback
                configs.extend([
                    ['arecord', '-f', 'S16_LE', '-r', '44100', '-c', '2'],
                    ['arecord', '-f', 'S16_LE', '-r', '16000', '-c', '1'],
                ])
                
                # Try each configuration
                for cmd in configs:
                    print(f"Trying: {' '.join(cmd)}")
                    
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    # Check if it started successfully
                    time.sleep(0.2)
                    if self.process.poll() is None:
                        print(f"✓ Recording started successfully!")
                        self.actual_sample_rate = int(cmd[4])
                        self.actual_channels = int(cmd[6])
                        print(f"Format: {self.actual_sample_rate} Hz, {self.actual_channels} channel(s)")
                        break
                    else:
                        stderr = self.process.stderr.read().decode()
                        print(f"✗ Failed: {stderr.strip()}")
                
                # Check for immediate errors
                time.sleep(0.1)
                if self.process.poll() is not None:
                    stderr = self.process.stderr.read().decode()
                    print(f"Recording failed immediately: {stderr}")
                    return
                
                # Read audio data
                bytes_read = 0
                chunks_read = 0
                while self.recording and self.process.poll() is None:
                    data = self.process.stdout.read(1024)
                    if data:
                        self.audio_data.append(data)
                        bytes_read += len(data)
                        chunks_read += 1
                        # Reduced logging - only every ~5 seconds
                        if chunks_read % 250 == 0:  
                            print(f"Recording... {bytes_read/1024:.1f} KB captured")
                
                print(f"Recording stopped. Total: {bytes_read/1024:.1f} KB in {chunks_read} chunks")
                
            except Exception as e:
                print(f"Recording error: {e}")
                import traceback
                traceback.print_exc()
        
        self.record_thread = threading.Thread(target=record_thread, daemon=True)
        self.record_thread.start()
    
    def stop_recording(self):
        """Stop recording and return audio data."""
        self.recording = False
        
        if hasattr(self, 'process'):
            self.process.terminate()
            self.process.wait()
        
        if hasattr(self, 'record_thread'):
            self.record_thread.join(timeout=1)
        
        # Combine audio data
        if self.audio_data:
            return b''.join(self.audio_data)
        return None
    
    def transcribe_audio(self, audio_data):
        """Transcribe audio data using Whisper."""
        if not audio_data:
            print("No audio data to transcribe")
            return None
        
        print(f"\nTranscribing {len(audio_data)/1024:.1f} KB of audio...")
        
        try:
            # Apply gain to audio data
            audio_gain = self.config.get('audio_gain', 1.0)
            if audio_gain != 1.0:
                print(f"Applying audio gain: {audio_gain}x")
                audio_data = self.apply_gain(audio_data, audio_gain)
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                # Write WAV header - use actual recorded format
                with wave.open(tmp.name, 'wb') as wav:
                    wav.setnchannels(self.actual_channels or 1)
                    wav.setsampwidth(2)  # 16-bit
                    wav.setframerate(self.actual_sample_rate or 16000)
                    wav.writeframes(audio_data)
                
                tmp_path = tmp.name
            
            # Try to use whisper CLI if available
            if self.check_whisper_cli():
                print("Using whisper CLI...")
                cmd = ['whisper', tmp_path, '--model', self.config.get('whisper_model', 'base'),
                       '--language', self.config.get('language', 'en'), '--task', 'transcribe']
                print(f"Command: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("Whisper CLI succeeded")
                    # Extract text from output
                    lines = result.stdout.strip().split('\n')
                    text = ' '.join(line.strip() for line in lines if line.strip())
                    os.unlink(tmp_path)
                    return text
                else:
                    print(f"Whisper CLI failed: {result.stderr}")
            
            # Fallback: try faster-whisper if available
            try:
                from faster_whisper import WhisperModel
                
                print("Using faster-whisper...")
                model_size = self.config.get('whisper_model', 'base')
                print(f"Loading model: {model_size}")
                
                model = WhisperModel(
                    model_size,
                    device='cpu',
                    compute_type='int8'
                )
                
                print(f"Transcribing with language: {self.config.get('language', 'en')}")
                # Use GUI settings for VAD
                silence_threshold = self.config.get('silence_threshold', 0.56)
                audio_threshold = self.config.get('audio_threshold', 0.006)
                
                # Convert GUI settings to Whisper parameters
                # silence_threshold (0-1) -> min_silence_duration_ms (100-1000ms)
                min_silence_ms = int(100 + (silence_threshold * 900))
                
                # audio_threshold (0-1) -> no_speech_threshold (0-1)
                no_speech_thresh = max(0.1, min(0.9, audio_threshold * 10))
                
                print(f"VAD settings - silence: {min_silence_ms}ms, speech threshold: {no_speech_thresh:.3f}")
                
                segments, info = model.transcribe(
                    tmp_path,
                    language=self.config.get('language', 'en'),
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=min_silence_ms,
                        speech_pad_ms=200,
                    ),
                    no_speech_threshold=no_speech_thresh,
                    condition_on_previous_text=False
                )
                
                # Collect segments
                all_segments = []
                for segment in segments:
                    all_segments.append(segment.text.strip())
                    print(f"Segment: {segment.text.strip()}")
                
                text = ' '.join(all_segments)
                print(f"Combined text: {text}")
                os.unlink(tmp_path)
                return text
                
            except ImportError as e:
                print(f"Whisper import error: {e}")
                print("Install with: pip install faster-whisper")
            
            os.unlink(tmp_path)
            
        except Exception as e:
            print(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def apply_gain(self, audio_data, gain):
        """Apply gain to audio data."""
        import numpy as np
        
        # Convert bytes to 16-bit integers
        samples = np.frombuffer(audio_data, dtype=np.int16)
        
        # Apply gain
        amplified = samples.astype(np.float32) * gain
        
        # Clip to prevent overflow
        amplified = np.clip(amplified, -32768, 32767)
        
        # Convert back to int16
        return amplified.astype(np.int16).tobytes()
    
    def check_whisper_cli(self):
        """Check if whisper CLI is available."""
        try:
            result = subprocess.run(['which', 'whisper'], capture_output=True)
            return result.returncode == 0
        except:
            return False


class AudioLevelMonitor:
    """Monitor audio levels in real-time."""
    
    @staticmethod
    def get_audio_level(audio_data):
        """Calculate RMS level from audio data."""
        if not audio_data:
            return 0.0
        
        # Convert bytes to 16-bit integers
        samples = struct.unpack(f'{len(audio_data)//2}h', audio_data)
        
        # Calculate RMS
        sum_squares = sum(s**2 for s in samples)
        rms = (sum_squares / len(samples)) ** 0.5
        
        # Normalize to 0-1 range
        return min(1.0, rms / 32768.0)