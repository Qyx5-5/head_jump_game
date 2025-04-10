import pygame
import math
from typing import Optional

class AssetManager:
    def __init__(self, config):
        self.config = config
        self.assets = {}
        self._generate_assets()

    def _generate_assets(self):
        print("Generating procedural assets...")
        self._generate_player_asset()
        self._generate_obstacle_assets()
        self._generate_powerup_assets()
        print(f"Assets generated: {list(self.assets.keys())}")

    def _generate_player_asset(self):
        player_config = self.config.get('player', {})
        size = player_config.get('size', 50)
        color = tuple(player_config.get('color', (0, 200, 0))) # Default bright green

        # Create a surface with per-pixel alpha
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        # Draw a simple circle character
        pygame.draw.circle(surface, color, (size // 2, size // 2), size // 2)
        # Add a simple 'eye'
        eye_size = size // 6
        pygame.draw.circle(surface, (255, 255, 255), (size * 2 // 3, size // 3), eye_size)
        pygame.draw.circle(surface, (0, 0, 0), (size * 2 // 3 + eye_size // 3, size // 3), eye_size // 2)
        
        self.assets['player'] = surface

    def _generate_obstacle_assets(self):
        obstacle_configs = self.config.get('obstacles', {})
        base_config = obstacle_configs.get('base', {})

        for name, config in obstacle_configs.items():
            if name == 'base' or 'gap' in name:
                continue # Skip base config and gaps

            # Use specific config, fall back to base, then to defaults
            width = config.get('width', base_config.get('width', 50))
            # Use average of min/max height for procedural generation for now
            h_min = config.get('height_min', base_config.get('height_min', 50))
            h_max = config.get('height_max', base_config.get('height_max', 100))
            height = (h_min + h_max) // 2 
            color = tuple(config.get('color', base_config.get('color', (255, 0, 0))))

            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            
            if name == 'low_cactus':
                # Draw a simple cactus shape
                pygame.draw.rect(surface, color, (0, 0, width, height))
                # Add some details (lines)
                for i in range(1, 4):
                    pygame.draw.line(surface, (0,0,0, 50), (width * i // 4, 5), (width * i // 4, height-5), 1)
            elif name == 'flying_rock':
                # Draw a rough rock shape (polygon)
                points = [
                    (0, height // 3), (width // 3, 0), (width * 2 // 3, 0), 
                    (width, height // 3), (width, height * 2 // 3), 
                    (width * 2 // 3, height), (width // 3, height), (0, height * 2 // 3)
                ]
                pygame.draw.polygon(surface, color, points)
                pygame.draw.polygon(surface, (0,0,0, 50), points, 2) # Outline
            else:
                 # Default to a rectangle
                 pygame.draw.rect(surface, color, (0, 0, width, height))

            self.assets[f'obstacle_{name}'] = surface

    def _generate_powerup_assets(self):
        powerup_configs = self.config.get('powerup', {}).get('types', {})
        default_color = (255, 255, 0) # Yellow default
        size = 20 # Fixed size for now, maybe make configurable later

        for name, config in powerup_configs.items():
            color = tuple(config.get('color', default_color))
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            center = (size // 2, size // 2)
            radius = size // 2

            if name == 'score_boost':
                # Draw a star
                points = []
                for i in range(5):
                    angle = math.pi / 2 - 2 * math.pi * i / 5
                    points.append((center[0] + radius * math.cos(angle), center[1] - radius * math.sin(angle)))
                    angle += math.pi / 5
                    points.append((center[0] + radius/2 * math.cos(angle), center[1] - radius/2 * math.sin(angle)))
                pygame.draw.polygon(surface, color, points)
            elif name == 'invincibility':
                # Draw a shield shape
                pygame.draw.rect(surface, color, (2, 0, size - 4, size - 4), border_top_left_radius=4, border_top_right_radius=4)
                pygame.draw.polygon(surface, color, [(2, size - 5), (size - 2, size - 5), center])
            elif name == 'slow_motion':
                 # Draw a clock face
                 pygame.draw.circle(surface, color, center, radius, 2) # Outline
                 pygame.draw.line(surface, color, center, (center[0], center[1] - radius * 0.7), 2) # Minute hand
                 pygame.draw.line(surface, color, center, (center[0] + radius * 0.5, center[1]), 1) # Hour hand
            else:
                 # Default to circle
                 pygame.draw.circle(surface, color, center, radius)

            self.assets[f'powerup_{name}'] = surface

    def get_asset(self, name: str) -> Optional[pygame.Surface]:
        asset = self.assets.get(name)
        if asset is None:
            print(f"Warning: Asset '{name}' not found.")
        return asset

    def get_obstacle_asset(self, obstacle_type: str) -> Optional[pygame.Surface]:
        return self.get_asset(f'obstacle_{obstacle_type}')

    def get_powerup_asset(self, powerup_type: str) -> Optional[pygame.Surface]:
        return self.get_asset(f'powerup_{powerup_type}')

    def get_player_asset(self) -> Optional[pygame.Surface]:
        return self.get_asset('player') 