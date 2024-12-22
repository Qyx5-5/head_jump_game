from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"

class LeaderboardManager:
    def __init__(self, filename="leaderboard.json"):
        self.filename = filename
        self.scores = self._load_scores()
    
    def add_score(self, player_name, score):
        self.scores.append({"name": player_name, "score": score})
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]  # Keep top 10
        self._save_scores()
    
    def get_top_scores(self, limit=10):
        return self.scores[:limit]
    
    def _load_scores(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_scores(self):
        with open(self.filename, 'w') as f:
            json.dump(self.scores, f) 