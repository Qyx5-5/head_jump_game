import cv2
import numpy as np
from datetime import datetime
from ..utils.game_utils import GameState

class Renderer:
    def __init__(self, config):
        self.config = config
        self.player_color = (0, 255, 0)
        self.obstacle_color = (255, 0, 0)
        self.background_x = 0
        self.background_speed = 2

    def render(self, frame, game_state):
        try:
            # Create a blank canvas for the game background (black)
            h, w = self.config.get('height', 720), self.config.get('width', 1280)
            rendered_frame = np.zeros((h, w, 3), dtype=np.uint8)
            
            # Draw background first
            self._draw_background(rendered_frame, w)
            
            # Validate game_state
            if not isinstance(game_state, dict) or 'state' not in game_state:
                print("Invalid game state:", game_state)
                return rendered_frame
            
            # Draw game elements based on state
            if game_state['state'] == GameState.MENU:
                self._draw_menu(rendered_frame)
            elif game_state['state'] == GameState.PLAYING:
                if 'player' in game_state and game_state['player'] is not None:
                    self._draw_player(rendered_frame, game_state['player'])
                
                if 'obstacles' in game_state:
                    for obstacle in game_state['obstacles']:
                        self._draw_obstacle(rendered_frame, obstacle)
                
                if 'power_ups' in game_state:
                    for power_up in game_state['power_ups']:
                        self._draw_powerup(rendered_frame, power_up)
                
                self._draw_hud(rendered_frame, game_state)
            elif game_state['state'] == GameState.GAME_OVER:
                # Draw final game state first (skip player if None)
                if 'player' in game_state and game_state['player'] is not None:
                    self._draw_player(rendered_frame, game_state['player'])
                
                if 'obstacles' in game_state:
                    for obstacle in game_state['obstacles']:
                        self._draw_obstacle(rendered_frame, obstacle)
                
                # Draw game over overlay
                self._draw_game_over(rendered_frame, game_state)
            
            # Add camera feed to top-right corner if available
            if frame is not None and frame.size > 0:
                try:
                    overlay_w = w // 4
                    overlay_h = h // 4
                    
                    # Resize camera feed to overlay size
                    camera_overlay = cv2.resize(frame, (overlay_w, overlay_h))
                    
                    # Calculate position for top-right corner
                    x_offset = w - overlay_w - 20
                    y_offset = 20
                    
                    # Create region of interest (ROI)
                    roi = rendered_frame[y_offset:y_offset+overlay_h, x_offset:x_offset+overlay_w]
                    
                    # Add semi-transparent black background
                    overlay_bg = np.zeros((overlay_h, overlay_w, 3), dtype=np.uint8)
                    cv2.addWeighted(roi, 0.7, overlay_bg, 0.3, 0, roi)
                    
                    # Overlay camera feed
                    rendered_frame[y_offset:y_offset+overlay_h, x_offset:x_offset+overlay_w] = camera_overlay
                    
                    # Add border around camera feed
                    cv2.rectangle(rendered_frame, 
                                (x_offset, y_offset), 
                                (x_offset+overlay_w, y_offset+overlay_h), 
                                (255, 255, 255), 2)
                except Exception as e:
                    print(f"Warning: Failed to add camera overlay: {e}")
            
            return rendered_frame
            
        except Exception as e:
            print(f"Error in render: {e}")
            # Return a basic error frame
            error_frame = np.zeros((self.config.get('height', 720), 
                                  self.config.get('width', 1280), 3), 
                                  dtype=np.uint8)
            cv2.putText(error_frame, f"Rendering Error: {str(e)}", 
                        (50, error_frame.shape[0]//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            return error_frame
    
    def _draw_background(self, frame, width):
        """Draw the game background"""
        # Update background position
        self.background_x -= self.background_speed
        if self.background_x < -width:
            self.background_x = 0
        
        # Draw dark background
        cv2.rectangle(frame, (0, 0), (width, frame.shape[0]), (40, 40, 40), -1)
        
        # Draw ground
        ground_y = frame.shape[0] - 100
        ground_color = (100, 100, 100)
        ground_thickness = 3
        
        # Draw ground pattern
        for i in range(0, width + 20, 20):  # +20 to ensure full coverage
            actual_x = (i + self.background_x) % width
            cv2.line(frame, 
                     (actual_x, ground_y), 
                     (actual_x + 10, ground_y), 
                     ground_color, 
                     ground_thickness)
    
    def _draw_player(self, frame, player_state):
        player_x = player_state['x']
        player_y = int(player_state['y'])
        player_size = player_state['size']
        ground_level = player_state['ground_level']
        
        # Player shadow
        cv2.ellipse(frame,
                    (player_x + player_size//2, ground_level),
                    (player_size//2, 10),
                    0, 0, 360,
                    (20, 20, 20),
                    -1)
        
        # Player body - more detailed
        player_color = (0, 255, 0)
        
        # Draw a triangle for the player
        pts = np.array([
            [player_x + player_size//2, player_y - player_size],
            [player_x, player_y],
            [player_x + player_size, player_y]
        ], np.int32)
        cv2.fillPoly(frame, [pts], player_color)
        cv2.polylines(frame, [pts], True, (0, 200, 0), 3)
        
        # Add a small circle for the head
        cv2.circle(frame, (player_x + player_size//2, player_y - player_size + 10), 10, (0, 200, 0), -1)
    
    def _draw_obstacle(self, frame, obs_state):
        # Obstacle shadow
        cv2.ellipse(frame,
                    (int(obs_state['x'] + obs_state['width']//2), int(self.config['height'] - 100)),
                    (int(obs_state['width']//2), 10),
                    0, 0, 360,
                    (20, 20, 20),
                    -1)
        
        # Obstacle body - more detailed
        obstacle_color = (255, 0, 0)
        
        # Draw a rounded rectangle for the obstacle
        cv2.rectangle(frame, 
                     (int(obs_state['x']), int(self.config['height'] - 100 - obs_state['height'])),
                     (int(obs_state['x'] + obs_state['width']), int(self.config['height'] - 100)),
                     obstacle_color, -1)
        cv2.rectangle(frame, 
                     (int(obs_state['x']), int(self.config['height'] - 100 - obs_state['height'])),
                     (int(obs_state['x'] + obs_state['width']), int(self.config['height'] - 100)),
                     (200, 0, 0), 3)
        
        # Add some spikes on top
        spike_height = 10
        for i in range(0, int(obs_state['width']), 10):
            spike_x = int(obs_state['x']) + i
            spike_y = int(self.config['height'] - 100 - obs_state['height'])
            pts = np.array([
                [spike_x, spike_y],
                [spike_x + 5, spike_y - spike_height],
                [spike_x + 10, spike_y]
            ], np.int32)
            cv2.fillPoly(frame, [pts], (200, 0, 0))
    
    def _draw_powerup(self, frame, powerup_state):
        power_up_x = int(powerup_state['x'])
        power_up_y = int(self.config['height'] - 100 - powerup_state['height'])
        power_up_width = powerup_state['width']
        power_up_height = powerup_state['height']
        
        # Draw a star for the powerup
        star_points = np.array([
            [power_up_x + power_up_width // 2, power_up_y],
            [power_up_x + power_up_width * 3 // 4, power_up_y + power_up_height // 3],
            [power_up_x + power_up_width, power_up_y + power_up_height // 3],
            [power_up_x + power_up_width * 5 // 8, power_up_y + power_up_height * 2 // 3],
            [power_up_x + power_up_width * 3 // 4, power_up_y + power_up_height],
            [power_up_x + power_up_width // 2, power_up_y + power_up_height * 5 // 6],
            [power_up_x + power_up_width // 4, power_up_y + power_up_height],
            [power_up_x, power_up_y + power_up_height * 2 // 3],
            [power_up_x + power_up_width // 8, power_up_y + power_up_height // 3],
            [power_up_x + power_up_width // 4, power_up_y + power_up_height // 3]
        ], np.int32)
        cv2.fillPoly(frame, [star_points], (0, 255, 255))
    
    def _draw_hud(self, frame, game_state):
        h, w = frame.shape[:2]
        
        # Draw score
        cv2.putText(frame, f"Score: {game_state['score']}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Only show controls reminder briefly at start
        if game_state['start_time'] and (datetime.now() - game_state['start_time']).total_seconds() < 5:
            cv2.putText(frame, "Move head UP to jump!", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    
    def _draw_menu(self, frame):
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 1.0, 0, frame)
        
        # Title - centered
        title = "Head Jump Game"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 2)[0]
        cv2.putText(frame, title, 
                    (w//2 - title_size[0]//2, h//3),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        # Instructions
        instructions = "Press Space to Start"
        instructions_size = cv2.getTextSize(instructions, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        cv2.putText(frame, instructions,
                    (w//2 - instructions_size[0]//2, h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    def _draw_game_over(self, frame, game_state):
        try:
            h, w = frame.shape[:2]
            
            # Semi-transparent overlay
            overlay = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 1.0, 0, frame)
            
            # Game Over text
            game_over_text = "Game Over"
            text_size = cv2.getTextSize(game_over_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0]
            cv2.putText(frame, game_over_text,
                        (w//2 - text_size[0]//2, h//3),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)
            
            # Show final score
            score = game_state.get('score', 0)  # Use get() with default value
            score_text = f"Final Score: {score}"
            score_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            cv2.putText(frame, score_text,
                        (w//2 - score_size[0]//2, h//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Instructions
            instructions = [
                "Press SPACE to Play Again",
                "Press ESC for Menu",
                "Press Q to Quit"
            ]
            
            y_offset = h//2 + 50
            for instruction in instructions:
                inst_size = cv2.getTextSize(instruction, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                cv2.putText(frame, instruction,
                            (w//2 - inst_size[0]//2, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                y_offset += 40
        except Exception as e:
            print(f"Error in _draw_game_over: {e}")