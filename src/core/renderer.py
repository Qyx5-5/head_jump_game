import cv2
import numpy as np
import pygame
from src.utils.game_utils import GameState

class Renderer:
    def __init__(self, config, asset_manager):
        self.config = config
        self.asset_manager = asset_manager
        self.width = config.get('width', 1280)
        self.height = config.get('height', 720)
        
        # Colors
        self.BACKGROUND_COLOR = (40, 40, 40)
        self.GROUND_COLOR = (100, 100, 100)
        self.OBSTACLE_COLOR = (255, 0, 0)
        self.POWERUP_COLOR = (255, 255, 0)
        
        # Background scrolling
        self.background_x = 0
        self.background_speed = 2
        
        # Initialize Pygame and create window
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Head Jump Game")
        
        # Initialize font
        self.font = pygame.font.Font(None, 36)

    def render(self, face_frame, game_state):
        """Main render function"""
        # Clear screen with background color
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # Draw background for all states
        self._draw_background()
        
        # Handle different game states
        if game_state['state'] == GameState.MENU:
            self._draw_menu()
        elif game_state['state'] == GameState.PLAYING:
            self._draw_game_elements(game_state)
        elif game_state['state'] == GameState.GAME_OVER:
            self._draw_game_elements(game_state)  # Show final state
            self._draw_game_over(game_state['score'])
        
        # Draw face frame if available
        if face_frame is not None:
            face_surface = self._convert_cv2_to_pygame(face_frame)
            self._draw_face_frame(face_surface)
        
        # Update display
        pygame.display.flip()
        
        # Convert to CV2 format for compatibility
        return self._pygame_surface_to_cv2(self.screen)

    def _draw_game_elements(self, game_state):
        """Draw all game elements"""
        # --- Player Drawing with Invincibility Effect ---
        player_sprite = None
        if game_state.get('all_sprites'):
             sprites = game_state['all_sprites'].sprites()
             if sprites:
                 player_sprite = sprites[0] # Assuming player is the first sprite

        is_invincible = game_state.get('is_invincible', False)
        original_alpha = None
        if player_sprite and is_invincible:
            try:
                # Make player semi-transparent during invincibility
                original_alpha = player_sprite.image.get_alpha()
                player_sprite.image.set_alpha(128) # 50% transparent
            except AttributeError: # Handle if image is not per-pixel alpha
                print("Warning: Cannot set alpha on player sprite image.")
                pass 
        
        if game_state.get('all_sprites'):
            game_state['all_sprites'].draw(self.screen) # Draw player (and potentially others)

        # Restore player alpha after drawing
        if player_sprite and original_alpha is not None:
             try:
                 player_sprite.image.set_alpha(original_alpha)
             except AttributeError:
                 pass
        # --- End Player Drawing ---

        # --- Obstacle Drawing using Assets ---
        for obstacle in game_state.get('obstacles', []):
            obstacle_type = obstacle.get('type')
            asset = self.asset_manager.get_obstacle_asset(obstacle_type)
            if asset:
                 # Adjust blit position if asset size differs from obstacle dict size
                 # For now, assuming asset matches config height/width used in engine
                 blit_x = int(obstacle['x'])
                 blit_y = int(obstacle['y'])
                 self.screen.blit(asset, (blit_x, blit_y))
            else:
                 # Fallback: Draw a red rectangle if asset is missing
                 pygame.draw.rect(self.screen,
                                (255, 0, 0), # Bright red fallback
                                pygame.Rect(
                                    int(obstacle['x']),
                                    int(obstacle['y']),
                                    obstacle['width'],
                                    obstacle['height']
                                ))
        # --- End Obstacle Drawing ---
        
        # --- Powerup Drawing using Assets ---
        for powerup in game_state.get('power_ups', []):
            powerup_type = powerup.get('type')
            asset = self.asset_manager.get_powerup_asset(powerup_type)
            if asset:
                blit_x = int(powerup['x'])
                blit_y = int(powerup['y'])
                self.screen.blit(asset, (blit_x, blit_y))
            else:
                # Fallback: Draw a yellow circle if asset is missing
                pygame.draw.circle(self.screen,
                                 self.POWERUP_COLOR, # Default yellow
                                 (int(powerup['x'] + powerup['width']//2),
                                  int(powerup['y'] + powerup['height']//2)),
                                 powerup.get('width', 20) // 2)
        # --- End Powerup Drawing ---
        
        # Draw score
        self._draw_score(game_state['score'])
        
        # Draw active powerup indicators
        self._draw_active_powerup_info(game_state)

    def _draw_menu(self):
        """Draw menu screen"""
        title = self.font.render('Head Jump Game', True, (255, 255, 255))
        start_text = self.font.render('Press SPACE to Start', True, (255, 255, 255))
        
        title_rect = title.get_rect(center=(self.width//2, self.height//3))
        start_rect = start_text.get_rect(center=(self.width//2, self.height//2))
        
        self.screen.blit(title, title_rect)
        self.screen.blit(start_text, start_rect)

    def _draw_game_over(self, score):
        """Draw game over screen"""
        game_over = self.font.render('Game Over', True, (255, 0, 0))
        score_text = self.font.render(f'Final Score: {score}', True, (255, 255, 255))
        restart_text = self.font.render('Press SPACE to Restart', True, (255, 255, 255))
        
        game_over_rect = game_over.get_rect(center=(self.width//2, self.height//3))
        score_rect = score_text.get_rect(center=(self.width//2, self.height//2))
        restart_rect = restart_text.get_rect(center=(self.width//2, 2*self.height//3))
        
        self.screen.blit(game_over, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(restart_text, restart_rect)

    def _draw_multiplier(self, multiplier):
        """Draw score multiplier"""
        multiplier_text = self.font.render(f'x{multiplier}', True, (255, 255, 0))
        self.screen.blit(multiplier_text, (10, 50))

    def _draw_background(self):
        """Draw the game background"""
        # Update background position
        self.background_x = (self.background_x - self.background_speed) % self.width
        
        # Draw ground
        ground_y = self.height - 100
        pygame.draw.line(self.screen, 
                        self.GROUND_COLOR,
                        (0, ground_y),
                        (self.width, ground_y),
                        3)
        
        # Draw ground pattern
        for i in range(0, self.width + 20, 20):
            actual_x = (i + self.background_x) % self.width
            pygame.draw.line(self.screen,
                           self.GROUND_COLOR,
                           (actual_x, ground_y),
                           (actual_x + 10, ground_y),
                           3)

    def _draw_score(self, score):
        """Draw the score"""
        score_text = self.font.render(f'Score: {score}', True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

    def _convert_cv2_to_pygame(self, cv2_image):
        """Convert OpenCV image to Pygame surface"""
        if cv2_image is None:
            return None
            
        # Resize face frame
        face_height = self.height // 4
        face_width = self.width // 4
        cv2_image = cv2.resize(cv2_image, (face_width, face_height))
        
        # Convert from BGR to RGB
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        
        # Create Pygame surface
        shape = cv2_image.shape[1::-1]  # width, height
        return pygame.image.frombuffer(cv2_image.tobytes(), shape, 'RGB')

    def _pygame_surface_to_cv2(self, pygame_surface):
        """Convert Pygame surface to OpenCV image (for compatibility)"""
        # Get the size of the surface
        size = pygame_surface.get_size()
        
        # Get raw pixel data
        view = pygame.surfarray.array3d(pygame_surface)
        
        # Convert from RGB to BGR
        view = view.transpose([1, 0, 2])
        img_bgr = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)
        
        return img_bgr

    def _draw_face_frame(self, face_surface):
        """Draw the face frame in the corner"""
        if face_surface is None:
            return
            
        # Calculate position (top-right corner)
        x_offset = self.width - face_surface.get_width() - 10
        y_offset = 10
        
        # Draw face frame
        self.screen.blit(face_surface, (x_offset, y_offset))

    def cleanup(self):
        """Clean up resources"""
        pass  # Pygame.quit() should be handled by the game engine

    # Add a new helper method for drawing active powerup info
    def _draw_active_powerup_info(self, game_state):
        y_offset = 50 # Start below score
        
        # Draw score multiplier if active
        multiplier = game_state.get('score_multiplier', 1.0)
        if multiplier > 1.0:
            color = self.config.get('powerup', {}).get('types', {}).get('score_boost', {}).get('color', (255, 255, 0))
            multiplier_text = self.font.render(f'Score x{multiplier:.1f}', True, tuple(color))
            self.screen.blit(multiplier_text, (10, y_offset))
            y_offset += 30
            
        # Draw invincibility indicator
        if game_state.get('is_invincible', False):
            color = self.config.get('powerup', {}).get('types', {}).get('invincibility', {}).get('color', (0, 255, 255))
            invincibility_text = self.font.render('Invincible!', True, tuple(color))
            self.screen.blit(invincibility_text, (10, y_offset))
            y_offset += 30
            
        # Draw slow motion indicator
        slow_factor = game_state.get('slow_motion_factor', 1.0)
        if slow_factor < 1.0:
            color = self.config.get('powerup', {}).get('types', {}).get('slow_motion', {}).get('color', (255, 0, 255))
            slow_text = self.font.render(f'Slow Motion ({slow_factor:.1f}x)', True, tuple(color))
            self.screen.blit(slow_text, (10, y_offset))
            y_offset += 30