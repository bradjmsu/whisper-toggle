#!/usr/bin/env python3
"""
Configuration management for Whisper Toggle
"""

import os
import json
from pathlib import Path

class Config:
    """Configuration manager with persistent storage."""
    
    def __init__(self):
        # Default configuration
        self.defaults = {
            'toggle_key': 'KEY_F16',
            'audio_device': 1,  # fifine Microphone
            'audio_gain': 1.0,
            'whisper_model': 'base',
            'silence_threshold': 0.75,
            'audio_threshold': 0.01,
            'start_minimized': True,
            'show_notifications': True,
            'play_sounds': True,
            'auto_start': False,
            'language': 'en',
            'continuous_mode': False,
            'output_method': 'type',
            # GPU/Performance settings
            'device': 'auto',  # auto, cpu, cuda
            'compute_type': 'auto',  # auto, int8, float16, float32
            'gpu_memory_limit': 0,  # 0 = no limit, >0 = GB limit
        }
        
        # Config file location
        self.config_dir = Path.home() / '.config' / 'whisper-toggle'
        self.config_file = self.config_dir / 'config.json'
        
        # Current configuration
        self.config = self.defaults.copy()
        
        # Load existing config
        self.load()
    
    def get(self, key, default=None):
        """Get configuration value."""
        return self.config.get(key, default or self.defaults.get(key))
    
    def set(self, key, value):
        """Set configuration value."""
        self.config[key] = value
    
    def load(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                
                # Update config with saved values
                self.config.update(saved_config)
                print(f"Loaded config from {self.config_file}")
            else:
                print("No config file found, using defaults")
        except Exception as e:
            print(f"Error loading config: {e}")
            # Use defaults if loading fails
    
    def save(self):
        """Save configuration to file."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save config to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            print(f"Saved config to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def reset(self):
        """Reset configuration to defaults."""
        self.config = self.defaults.copy()
        return self.save()
    
    # Properties for backward compatibility
    @property
    def toggle_key(self):
        return self.get('toggle_key')
    
    @property
    def audio_device(self):
        return self.get('audio_device')
    
    @property
    def audio_gain(self):
        return self.get('audio_gain')
    
    @property
    def whisper_model(self):
        return self.get('whisper_model')
    
    @property
    def silence_threshold(self):
        return self.get('silence_threshold')
    
    @property
    def audio_threshold(self):
        return self.get('audio_threshold')
    
    @property
    def start_minimized(self):
        return self.get('start_minimized')
    
    @property
    def show_notifications(self):
        return self.get('show_notifications')
    
    @property
    def play_sounds(self):
        return self.get('play_sounds')
    
    @property
    def auto_start(self):
        return self.get('auto_start')
    
    @property
    def language(self):
        return self.get('language')
    
    @property
    def continuous_mode(self):
        return self.get('continuous_mode')
    
    @property
    def output_method(self):
        return self.get('output_method')
    
    @property
    def device(self):
        return self.get('device')
    
    @property
    def compute_type(self):
        return self.get('compute_type')
    
    @property
    def gpu_memory_limit(self):
        return self.get('gpu_memory_limit')