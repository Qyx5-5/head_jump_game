from ..utils.game_utils import GameState
from ..entities.player import Player
from datetime import datetime
import numpy as np

class GameEngine:
    def __init__(self, config, game_state=GameState.MENU):
        self.config = config
        self.game_state = game_state
        self.player = Player(config)  # Initialize from config
        self.obstacles = []
        self.power_ups = []
        self.score = 0
        self.start_time = None
        self.current_level = 0
        self.distance_traveled = 0
        self.score_multiplier = 1.0
        self.spawn_timer = 0
        self.power_up_timer = 0
        self.power_up_duration = 5 # seconds
        self.power_up_active = False
        
        # Load config
        self.obstacle_speed = self.config.get('obstacle_speed', 12)
        self.min_spawn_interval = self.config.get('min_spawn_interval', 45)

    def update(self, dt, nose_point=None):
        if self.game_state != GameState.PLAYING:
            return
        
        if self.start_time is None:
            self.start_time = datetime.now()
        
        # Update player
        self.player.update(dt, nose_point)

        # Spawn and update obstacles
        self._spawn_obstacles()
        self._update_obstacles()
        
        # Spawn and update powerups
        self._spawn_powerups()
        self._update_powerups()

        # Check for collisions
        self._check_collisions()

        # Update score
        self._update_score()
        
        # Check if powerup duration is over
        if self.power_up_active:
            if (datetime.now() - self.power_up_timer).total_seconds() > self.power_up_duration:
                self.score_multiplier = 1.0
                self.power_up_active = False

    def _spawn_obstacles(self):
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
                    'x': self.config['width'] - 50,
                    'width': width,
                    'height': height,
                    'speed': self.obstacle_speed
                })
                self.spawn_timer = 0
    
    def _update_obstacles(self):
        for obstacle in self.obstacles:
            obstacle['x'] -= obstacle['speed']
        
        # Remove off-screen obstacles
        self.obstacles = [obs for obs in self.obstacles if obs['x'] + obs['width'] > 0]
    
    def _spawn_powerups(self):
        if np.random.random() < 0.1: # 10% chance to spawn powerup
            self.power_ups.append({
                'x': self.config['width'] - 50,
                'type': 'score_boost',
                'width': 20,
                'height': 20,
                'speed': self.obstacle_speed
            })
    
    def _update_powerups(self):
        for power_up in self.power_ups:
            power_up['x'] -= power_up['speed']
        
        # Remove off-screen powerups
        self.power_ups = [power_up for power_up in self.power_ups if power_up['x'] + power_up['width'] > 0]
    
    def _check_collisions(self):
        player_rect = self.player.get_rect()
        
        for obstacle in self.obstacles:
            if self._check_collision(player_rect, obstacle):
                self.game_state = GameState.GAME_OVER
                return
        
        for power_up in self.power_ups:
            if self._check_collision(player_rect, power_up):
                if power_up['type'] == 'score_boost':
                    self.score_multiplier = 2.0
                    self.power_up_active = True
                    self.power_up_timer = datetime.now()
                self.power_ups.remove(power_up)
                
    def _check_collision(self, rect1, rect2):
        return (rect1['x'] < rect2['x'] + rect2['width'] and
                rect1['x'] + rect1['width'] > rect2['x'] and
                rect1['y'] < self.player.ground_level - rect2['height'] + rect2['height'] and
                rect1['y'] + rect1['height'] > self.player.ground_level - rect2['height'])
    
    def _update_score(self):
        self.score += int(1 * self.score_multiplier)
        self.distance_traveled += self.obstacle_speed
        if self.player.is_jumping == False:
            self.score += int(5 * self.score_multiplier) # Award points for landing

    def get_game_state(self):
        return {
            'state': self.game_state,
            'player': self.player.get_state() if self.game_state == GameState.PLAYING else None,
            'obstacles': self.obstacles,
            'power_ups': self.power_ups,
            'score': self.score,
            'game_state': self.game_state,
            'current_level': self.current_level,
            'distance_traveled': self.distance_traveled,
            'score_multiplier': self.score_multiplier,
            'power_up_active': self.power_up_active,
            'power_up_timer': self.power_up_timer,
            'power_up_duration': self.power_up_duration,
            'start_time': self.start_time
        } 