from enum import Enum
from datetime import datetime

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"

class GameStateManager:
    def __init__(self, engine):
        self.engine = engine
        self.current_state = GameState.MENU
        self.previous_state = None
        self.state_changed_time = datetime.now()

    def transition_to(self, new_state):
        """Handle state transitions with proper cleanup/initialization"""
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_changed_time = datetime.now()

        if new_state == GameState.PLAYING:
            if self.previous_state == GameState.MENU:
                self.engine.reset()
            self.engine.start_time = datetime.now()
        elif new_state == GameState.GAME_OVER:
            # Handle game over logic
            pass

    def get_current_state(self):
        return self.current_state

    def get_state_duration(self):
        return (datetime.now() - self.state_changed_time).total_seconds() 