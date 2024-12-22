from ..utils.game_utils import GameState
from ..entities.player import Player
from datetime import datetime
import numpy as np
from .obstacle_manager import ObstacleManager
from .powerup_manager import PowerUpManager

class GameEngine:
    def __init__(self, config, game_state=GameState.MENU):
        self.config = config
        self._game_state = game_state  # Private state variable
        self.player = Player(config)
        self.obstacle_manager = ObstacleManager(config)
        self.powerup_manager = PowerUpManager(config)
        self.score = 0
        self.start_time = None
        self.current_level = 0
        self.distance_traveled = 0
        
        # Load config
        self.obstacle_speed = self.config.get('game', {}).get('obstacle_speed', 12)
        self.min_spawn_interval = self.config.get('game', {}).get('min_spawn_interval', 45)

    @property
    def game_state(self):
        """Property to access game state"""
        return self._game_state

    @game_state.setter
    def game_state(self, new_state):
        """Setter for game state with validation"""
        if not isinstance(new_state, GameState):
            raise ValueError(f"Invalid game state: {new_state}")
        self._game_state = new_state

    def get_game_state(self):
        """Get complete game state dictionary"""
        return {
            'state': self._game_state,
            'player': self.player.get_state() if self._game_state == GameState.PLAYING else None,
            'obstacles': self.obstacle_manager.get_obstacles(),
            'power_ups': self.powerup_manager.get_powerups(),
            'score': self.score,
            'current_level': self.current_level,
            'distance_traveled': self.distance_traveled,
            'score_multiplier': self.powerup_manager.get_score_multiplier(),
            'power_up_active': self.powerup_manager.is_active(),
            'start_time': self.start_time
        }

    def update(self, dt, nose_point=None):
        if self._game_state != GameState.PLAYING:
            return
        
        if self.start_time is None:
            self.start_time = datetime.now()
        
        # Update player
        self.player.update(dt, nose_point)

        # Update obstacles and powerups
        self.obstacle_manager.update(self.start_time)
        self.powerup_manager.update()

        # Check for collisions
        self._check_collisions()

        # Update score
        self._update_score()

    def _check_collisions(self):
        player_rect = self.player.get_rect()
        
        # Check obstacle collisions
        for obstacle in self.obstacle_manager.get_obstacles():
            if self._check_collision(player_rect, obstacle):
                self.game_state = GameState.GAME_OVER
                return
        
        # Check powerup collisions
        for power_up in self.powerup_manager.get_powerups():
            if self._check_collision(player_rect, power_up):
                self.powerup_manager.handle_collision(power_up)

    def _update_score(self):
        multiplier = self.powerup_manager.get_score_multiplier()
        self.score += int(1 * multiplier)
        self.distance_traveled += self.obstacle_speed
        if not self.player.is_jumping:
            self.score += int(5 * multiplier)

    def reset(self):
        """Reset the game state while keeping the same instance"""
        self.obstacle_manager.reset()
        self.powerup_manager.reset()
        self.score = 0
        self.start_time = None
        self.current_level = 0
        self.distance_traveled = 0

    def _check_collision(self, rect1, rect2):
        return (rect1['x'] < rect2['x'] + rect2['width'] and
                rect1['x'] + rect1['width'] > rect2['x'] and
                rect1['y'] < self.player.ground_level - rect2['height'] + rect2['height'] and
                rect1['y'] + rect1['height'] > self.player.ground_level - rect2['height'])