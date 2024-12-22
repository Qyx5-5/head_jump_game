from datetime import datetime
import numpy as np

class PowerUpManager:
    def __init__(self, config):
        self.config = config
        self.power_ups = []
        self.power_up_active = False
        self.power_up_timer = None
        self.power_up_duration = config.get('powerup', {}).get('duration', 5)
        self.score_multiplier = 1.0
        self.obstacle_speed = config.get('game', {}).get('obstacle_speed', 12)

    def update(self):
        """Update powerups and their effects"""
        self._spawn_powerups()
        self._update_positions()
        self._check_duration()

    def _spawn_powerups(self):
        """Handle powerup spawning logic"""
        if np.random.random() < 0.1:  # 10% chance to spawn powerup
            self.power_ups.append({
                'x': self.config.get('width', 1280) - 50,
                'type': 'score_boost',
                'width': 20,
                'height': 20,
                'speed': self.obstacle_speed
            })

    def _update_positions(self):
        """Update positions of all powerups"""
        for power_up in self.power_ups:
            power_up['x'] -= power_up['speed']
        
        # Remove off-screen powerups
        self.power_ups = [p for p in self.power_ups if p['x'] + p['width'] > 0]

    def _check_duration(self):
        """Check if active powerup has expired"""
        if self.power_up_active and self.power_up_timer:
            if (datetime.now() - self.power_up_timer).total_seconds() > self.power_up_duration:
                self.deactivate_powerup()

    def handle_collision(self, power_up):
        """Handle powerup collection"""
        if power_up['type'] == 'score_boost':
            self.power_up_active = True
            self.power_up_timer = datetime.now()
            self.score_multiplier = self.config.get('powerup', {}).get('score_multiplier', 2.0)
        self.power_ups.remove(power_up)

    def get_powerups(self):
        """Return current powerups"""
        return self.power_ups

    def get_score_multiplier(self):
        """Return current score multiplier"""
        return self.score_multiplier

    def is_active(self):
        """Return whether a powerup is currently active"""
        return self.power_up_active

    def deactivate_powerup(self):
        """Deactivate current powerup"""
        self.power_up_active = False
        self.score_multiplier = 1.0
        self.power_up_timer = None

    def reset(self):
        """Reset the powerup manager state"""
        self.power_ups = []
        self.power_up_active = False
        self.power_up_timer = None
        self.score_multiplier = 1.0 