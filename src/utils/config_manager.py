from pathlib import Path
import json
from typing import Dict, Any

class ConfigManager:
    DEFAULT_CONFIG = {
        "video": {
            "width": 1280,
            "height": 720,
            "target_fps": 60,
            "camera_id": 0
        },
        "game": {
            "gravity": 2.0,
            "jump_strength": -25,
            "movement_threshold": 30,
            "obstacle_speed": 12,
            "min_spawn_interval": 45
        },
        "player": {
            "initial_x": 100,
            "size": 50,
            "ground_level_offset": 100
        },
        "powerup": {
            "duration": 5,
            "score_multiplier": 2.0
        }
    }

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load and validate configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                config = self._merge_with_defaults(loaded_config)
            else:
                print(f"Config file not found at {self.config_path}, using defaults")
                config = self.DEFAULT_CONFIG.copy()
                config['width'] = config['video']['width']
                config['height'] = config['video']['height']
            return config
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}, using defaults")
            config = self.DEFAULT_CONFIG.copy()
            config['width'] = config['video']['width']
            config['height'] = config['video']['height']
            return config
        except Exception as e:
            print(f"Unexpected error loading config: {e}, using defaults")
            config = self.DEFAULT_CONFIG.copy()
            config['width'] = config['video']['width']
            config['height'] = config['video']['height']
            return config

    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults, ensuring all required values exist"""
        merged = self.DEFAULT_CONFIG.copy()
        for section, values in loaded_config.items():
            if section in merged and isinstance(merged[section], dict) and isinstance(values, dict):
                # Update existing sections (like 'video', 'game', etc.)
                merged[section].update(values)
            else:
                # Add new sections (like 'obstacles', 'difficulty')
                merged[section] = values
        
        # Ensure top-level width/height are present for compatibility if needed elsewhere
        if 'video' in merged:
             merged['width'] = merged['video'].get('width', 1280) # Use .get for safety
             merged['height'] = merged['video'].get('height', 720)
        return merged

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Safely get a config value with fallback to default"""
        try:
            return self.config[section][key]
        except KeyError:
            if default is not None:
                return default
            return self.DEFAULT_CONFIG[section][key]

    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            required_types = {
                "video": {
                    "width": int,
                    "height": int,
                    "target_fps": int,
                    "camera_id": int
                },
                "game": {
                    "gravity": (int, float),
                    "jump_strength": (int, float),
                    "movement_threshold": (int, float),
                    "obstacle_speed": (int, float),
                    "min_spawn_interval": int
                }
            }

            for section, type_dict in required_types.items():
                for key, expected_type in type_dict.items():
                    value = self.get(section, key)
                    if not isinstance(value, expected_type):
                        print(f"Invalid type for {section}.{key}: expected {expected_type}, got {type(value)}")
                        return False
            return True
        except Exception as e:
            print(f"Error validating config: {e}")
            return False 