import json
import os
from pathlib import Path


class Config:
    """Manages application configuration from JSON file"""
    
    DEFAULT_CONFIG = {
        "active_button_bg": "#4a90d9",
        "inactive_button_bg": "#606060",
        "bar_height": 50,
        "button_height": 1,
        "combobox_ipady": 1,
        "layout_mode": "buttons"  # "buttons" = buttons + all windows combobox, "comboboxes" = 4 desktop window comboboxes
    }
    
    def __init__(self):
        self.config_path = Path.home() / ".config" / "KosDWM" / "config.json"
        self.config = self.load()
    
    def load(self):
        """Load config from file, create defaults if not exists"""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.save(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return self._merge_with_defaults(config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}, using defaults")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_with_defaults(self, config):
        """Merge loaded config with defaults for any missing keys"""
        merged = self.DEFAULT_CONFIG.copy()
        merged.update(config)
        return merged
    
    def save(self, config=None):
        """Save config to file"""
        if config is None:
            config = self.config
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get a config value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a config value"""
        self.config[key] = value
        self.save()
