from datetime import datetime
import numpy as np

class ObstacleManager:
    def __init__(self, config):
        self.config = config
        self.obstacles = []
        self.spawn_timer = 0
        self.start_time = None
        self.obstacle_speed = config.get('game', {}).get('obstacle_speed', 12)
        self.min_spawn_interval = config.get('game', {}).get('min_spawn_interval', 45)
        self.current_level = 0

    def update(self, start_time):
        """Update all obstacles and handle spawning"""
        self.start_time = start_time
        self._spawn_obstacles()
        self._update_positions()
        
    def _spawn_obstacles(self):
        """Handle obstacle spawning logic"""
        self.spawn_timer += 1
        if self.spawn_timer >= self.min_spawn_interval:
            # Increase spawn chance over time
            base_chance = 0.3
            time_factor = 0.002
            spawn_chance = min(base_chance + 
                             (datetime.now() - self.start_time).total_seconds() * time_factor, 
                             0.6)
            
            # Increase obstacle speed based on level
            self.obstacle_speed = 12 + (self.current_level * 2)
            
            if np.random.random() < spawn_chance:
                self._create_obstacle()
                self.spawn_timer = 0

    def _create_obstacle(self):
        """Create a new obstacle with random properties"""
        obstacle_type = np.random.choice(['tall', 'short', 'wide'])
        if obstacle_type == 'tall':
            height = np.random.randint(80, 120)
            width = 30
        elif obstacle_type == 'short':
            height = np.random.randint(30, 60)
            width = 40
        else:  # wide
            height = np.random.randint(50, 80)
            width = 60
            
        self.obstacles.append({
            'x': self.config.get('width', 1280) - 50,
            'width': width,
            'height': height,
            'speed': self.obstacle_speed
        })

    def _update_positions(self):
        """Update positions of all obstacles"""
        for obstacle in self.obstacles:
            obstacle['x'] -= obstacle['speed']
        
        # Remove off-screen obstacles
        self.obstacles = [obs for obs in self.obstacles if obs['x'] + obs['width'] > 0]

    def get_obstacles(self):
        """Return current obstacles"""
        return self.obstacles

    def reset(self):
        """Reset the obstacle manager state"""
        self.obstacles = []
        self.spawn_timer = 0
        self.start_time = None
        self.obstacle_speed = self.config.get('game', {}).get('obstacle_speed', 12)
        self.current_level = 0

    def set_level(self, level):
        """Update the current level"""
        self.current_level = level 