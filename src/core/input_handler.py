from datetime import datetime
from src.utils.game_utils import GameState
from src.core.engine import GameEngine

class InputHandler:
    def __init__(self, game_engine, renderer, leaderboard):
        self.game_engine = game_engine
        self.renderer = renderer
        self.leaderboard = leaderboard
        self.player_name = "Player"
        self.stats_enabled = True
        self.debug_mode = False

    def handle_input(self, key):
        """Handle keyboard input and return whether the game should continue"""
        if key == -1:  # No key pressed
            return True
            
        key = key & 0xFF  # Mask to get ASCII value
        
        if key == ord('q'):
            print("Quitting the video stream.")
            return False
        elif key == ord('s'):
            self.stats_enabled = not self.stats_enabled
            print(f"Stats: {'On' if self.stats_enabled else 'Off'}")
        elif key == ord(' '):  # Space
            print(f"DEBUG: Space pressed! Current game state: {self.game_engine.game_state}")
            if self.game_engine.game_state == GameState.MENU:
                print("DEBUG: Transitioning from MENU to PLAYING")
                self.game_engine.game_state = GameState.PLAYING
                self.game_engine.start_time = datetime.now()
            elif self.game_engine.game_state == GameState.GAME_OVER:
                print("DEBUG: Transitioning from GAME_OVER to MENU")
                self.game_engine.reset()
                self.game_engine.game_state = GameState.MENU
        elif key == 27:  # ESC
            if self.game_engine.game_state == GameState.PLAYING:
                self.game_engine.game_state = GameState.MENU
            elif self.game_engine.game_state == GameState.GAME_OVER:
                self.game_engine.reset()
                self.game_engine.game_state = GameState.MENU
        elif key == ord('n'):  # Enter name
            self.player_name = input("Enter player name: ")
        elif key == ord('l'):  # Leaderboard
            print("Leaderboard:")
            for entry in self.leaderboard.get_top_scores():
                print(f"{entry['name']}: {entry['score']}")
        elif key == ord('d'):  # Debug mode
            self.debug_mode = not self.debug_mode
            print(f"Debug mode: {'On' if self.debug_mode else 'Off'}")
        
        return True

    def get_stats_enabled(self):
        return self.stats_enabled

    def get_debug_mode(self):
        return self.debug_mode

    def get_player_name(self):
        return self.player_name 