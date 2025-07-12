"""
Configuration management for Whisper Toggle.

Handles loading, saving, and managing application settings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Manages application configuration."""
    
    DEFAULT_CONFIG = {
        'toggle_key': 'KEY_F16',  # Default to F16 (X button on Keychron)
        'audio_device': None,  # None means auto-detect
        'whisper_model': 'base',
        'silence_threshold': 0.75,  # seconds
        'audio_threshold': 0.01,  # audio level threshold
        'start_minimized': True,
        'show_notifications': True,
        'play_sounds': True,
        'auto_start': False,
        'language': 'en',  # Whisper language code
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Use XDG config directory
            config_dir = Path.home() / '.config' / 'whisper-toggle'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / 'config.yaml'
        
        self.config = self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f) or {}
                # Merge with defaults to ensure all keys exist
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded_config)
                return config
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            config = self.DEFAULT_CONFIG.copy()
            self.save(config)
            return config
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self.config.update(updates)
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
    
    @property
    def toggle_key(self) -> str:
        return self.config['toggle_key']
    
    @property
    def audio_device(self) -> Optional[int]:
        return self.config['audio_device']
    
    @property
    def whisper_model(self) -> str:
        return self.config['whisper_model']
    
    @property
    def silence_threshold(self) -> float:
        return self.config['silence_threshold']
    
    @property
    def audio_threshold(self) -> float:
        return self.config['audio_threshold']
    
    @property
    def start_minimized(self) -> bool:
        return self.config['start_minimized']
    
    @property
    def show_notifications(self) -> bool:
        return self.config['show_notifications']
    
    @property
    def play_sounds(self) -> bool:
        return self.config['play_sounds']
    
    @property
    def auto_start(self) -> bool:
        return self.config['auto_start']
    
    @property
    def language(self) -> str:
        return self.config['language']