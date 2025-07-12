#!/usr/bin/env python3
"""
Smart audio device detection that works universally.
Maps between different audio APIs and finds the best device automatically.
"""

import subprocess
import re
import json
from pathlib import Path

class SmartAudioDevice:
    """Universal audio device detection and mapping."""
    
    def __init__(self):
        self.devices = []
        self.device_map = {}
        self._detect_devices()
    
    def _detect_devices(self):
        """Detect all audio devices using multiple methods."""
        # Method 1: arecord -l (ALSA)
        self._detect_alsa_devices()
        
        # Method 2: pactl (PulseAudio)
        self._detect_pulse_devices()
        
        # Method 3: Check /proc/asound
        self._detect_proc_devices()
        
        # Build smart mapping
        self._build_device_map()
    
    def _detect_alsa_devices(self):
        """Detect devices using ALSA (arecord -l)."""
        try:
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'card' in line and ':' in line:
                        match = re.search(r'card (\d+): (.+?) \[(.+?)\]', line)
                        if match:
                            card_num = int(match.group(1))
                            card_id = match.group(2)
                            card_name = match.group(3)
                            
                            device = {
                                'index': card_num,
                                'alsa_card': card_num,
                                'alsa_id': card_id,
                                'name': card_name,
                                'api': 'alsa',
                                'device_string': f'plughw:{card_num},0'
                            }
                            
                            # Categorize device
                            name_lower = card_name.lower()
                            if any(usb in name_lower for usb in ['usb', 'fifine', 'blue', 'yeti', 'webcam']):
                                device['category'] = 'usb'
                                device['priority'] = 1  # Prefer USB mics
                            elif 'hdmi' in name_lower:
                                device['category'] = 'hdmi'
                                device['priority'] = 10  # Avoid HDMI
                            else:
                                device['category'] = 'builtin'
                                device['priority'] = 5
                            
                            self.devices.append(device)
                            
        except Exception as e:
            print(f"ALSA detection failed: {e}")
    
    def _detect_pulse_devices(self):
        """Detect devices using PulseAudio."""
        try:
            # Get PulseAudio sources
            result = subprocess.run(['pactl', 'list', 'sources', 'short'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        source_name = parts[1]
                        
                        # Skip monitors
                        if '.monitor' in source_name:
                            continue
                        
                        # Try to match with ALSA devices
                        for device in self.devices:
                            if device['alsa_id'] in source_name:
                                device['pulse_index'] = i
                                device['pulse_name'] = source_name
                                break
                                
        except Exception:
            # PulseAudio might not be running
            pass
    
    def _detect_proc_devices(self):
        """Detect devices from /proc/asound."""
        try:
            asound_path = Path('/proc/asound')
            if asound_path.exists():
                # Get card info
                cards_file = asound_path / 'cards'
                if cards_file.exists():
                    content = cards_file.read_text()
                    for line in content.split('\n'):
                        if line.strip():
                            match = re.match(r'\s*(\d+)\s+\[(.+?)\s*\]:\s+(.+)', line)
                            if match:
                                card_num = int(match.group(1))
                                # Update existing device info
                                for device in self.devices:
                                    if device['alsa_card'] == card_num:
                                        device['driver'] = match.group(3).strip()
                                        break
                                        
        except Exception:
            pass
    
    def _build_device_map(self):
        """Build a smart mapping of device indices."""
        # Sort devices by priority (USB mics first, HDMI last)
        self.devices.sort(key=lambda d: d.get('priority', 99))
        
        # Create mappings
        for i, device in enumerate(self.devices):
            # Map "friendly index" to actual device
            self.device_map[i] = device
            
            # Also map by name patterns
            name_lower = device['name'].lower()
            if 'fifine' in name_lower:
                self.device_map['fifine'] = device
            elif 'yeti' in name_lower:
                self.device_map['yeti'] = device
            elif 'webcam' in name_lower:
                self.device_map['webcam'] = device
    
    def get_device_string(self, device_index_or_name):
        """Get the correct device string for arecord."""
        if device_index_or_name is None:
            # Return None to use default device
            return None
        
        # Try to find device
        device = None
        
        # Check if it's a direct card number
        if isinstance(device_index_or_name, int):
            # First check if it's a friendly index
            if device_index_or_name in self.device_map:
                device = self.device_map[device_index_or_name]
            else:
                # Maybe it's an actual ALSA card number
                for d in self.devices:
                    if d['alsa_card'] == device_index_or_name:
                        device = d
                        break
        
        # Check if it's a name
        elif isinstance(device_index_or_name, str):
            device_lower = device_index_or_name.lower()
            if device_lower in self.device_map:
                device = self.device_map[device_lower]
            else:
                # Search by partial name match
                for d in self.devices:
                    if device_lower in d['name'].lower():
                        device = d
                        break
        
        if device:
            return device['device_string']
        
        # Fallback - try as raw card number
        return f'plughw:{device_index_or_name},0'
    
    def get_best_device(self):
        """Get the best available recording device."""
        # Prefer USB microphones
        for device in self.devices:
            if device.get('category') == 'usb':
                return device
        
        # Then built-in mics
        for device in self.devices:
            if device.get('category') == 'builtin':
                return device
        
        # Return first available
        return self.devices[0] if self.devices else None
    
    def list_devices(self):
        """List all detected devices with friendly indices."""
        print("\n=== Available Audio Devices ===")
        for i, device in enumerate(self.devices):
            print(f"{i}: {device['name']} ({device['category']})")
            print(f"   ALSA: {device['device_string']}")
            if 'pulse_name' in device:
                print(f"   PulseAudio: {device['pulse_name']}")
            print()
    
    def save_mapping(self, config_path):
        """Save device mapping to config."""
        mapping = {
            'device_map': {
                str(k): {
                    'name': v['name'],
                    'alsa_card': v['alsa_card'],
                    'device_string': v['device_string']
                }
                for k, v in self.device_map.items()
                if isinstance(k, int)
            }
        }
        
        config_file = Path(config_path) / 'audio_devices.json'
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(mapping, indent=2))
        print(f"Device mapping saved to {config_file}")


# Test the smart detection
if __name__ == "__main__":
    detector = SmartAudioDevice()
    detector.list_devices()
    
    print("\n=== Testing device resolution ===")
    test_values = [0, 1, 2, 'fifine', 'webcam']
    for val in test_values:
        device_string = detector.get_device_string(val)
        print(f"Device '{val}' -> {device_string}")
    
    best = detector.get_best_device()
    if best:
        print(f"\nBest device: {best['name']} ({best['device_string']})")