import pygame
from collections import deque

class Player(pygame.sprite.Sprite):
    """Represents the player character in the game."""

    def __init__(self, config, asset_manager):
        """Initialize the player."""
        super().__init__()
        self.config = config
        self.asset_manager = asset_manager # Store asset_manager
        
        player_config = config.get('player', {})
        game_config = config.get('game', {})
        video_config = config.get('video', {})

        # Appearance and Position
        self.size = player_config.get('size', 50)
        
        # Get player asset from AssetManager
        player_asset = self.asset_manager.get_player_asset()
        if player_asset:
             self.original_image = player_asset # Keep original for effects
             self.image = self.original_image.copy()
        else:
             # Fallback to generating a simple surface if asset is missing
             print("Warning: Player asset not found, creating fallback.")
             self.image = pygame.Surface([self.size, self.size], pygame.SRCALPHA)
             self.image.fill(tuple(player_config.get('color', (0, 255, 0))))
             self.original_image = self.image # Treat fallback as original
             
        self.rect = self.image.get_rect()
        
        # Movement Attributes
        self.rect.x = player_config.get('initial_x', 100)
        self.ground_level = video_config.get('height', 720) - player_config.get('ground_offset', 100) # Renamed for clarity
        self.rect.bottom = self.ground_level
        self.jump_velocity = 0
        self.gravity = game_config.get('gravity', 2.0)
        self.jump_strength = game_config.get('jump_strength', -25) # Base jump strength
        self.is_jumping = False

        # Input Smoothing
        self.nose_y_history = deque(maxlen=player_config.get('smoothing_window', 3)) # Configurable smoothing window
        self.prev_smoothed_y = None
        self.movement_threshold = player_config.get('jump_threshold', 30) # Renamed for clarity

    def update(self, dt, nose_point=None):
        """Update the player's state based on nose input and physics."""
        smoothed_y = None
        current_jump_strength = self.jump_strength # Default to base strength

        if nose_point is not None:
            current_y = nose_point[1]
            self.nose_y_history.append(current_y)

            # Calculate smoothed position only when deque is full
            if len(self.nose_y_history) == self.nose_y_history.maxlen:
                smoothed_y = sum(self.nose_y_history) / len(self.nose_y_history)

                # Initialize previous smoothed position on the first full deque
                if self.prev_smoothed_y is None:
                    self.prev_smoothed_y = smoothed_y

                # Calculate movement based on smoothed values
                # Negative movement indicates upward motion
                movement = smoothed_y - self.prev_smoothed_y

                # --- Optional: Variable Jump Strength ---
                # Check if variable jump is enabled in config (add this to config if desired)
                if self.config.get('player', {}).get('variable_jump_enabled', False):
                     # Calculate how much the threshold was exceeded
                     exceed_amount = -movement - self.movement_threshold
                     # Normalize this amount (e.g., threshold=30, movement=-50 -> exceed=20)
                     # Max boost factor (e.g., 0.3 means up to 30% stronger jump)
                     max_boost_factor = self.config.get('player', {}).get('variable_jump_boost', 0.2)
                     # Scale factor (how quickly boost increases with faster movement)
                     boost_scale = self.config.get('player', {}).get('variable_jump_scale', 50.0)
                     # Calculate boost modifier (capped between 0 and max_boost_factor)
                     variable_jump_mod = max(0, min(max_boost_factor, exceed_amount / boost_scale))
                     # Apply the boost (making jump_strength more negative)
                     current_jump_strength = self.jump_strength * (1 + variable_jump_mod)
                # --- End Optional ---

                # Detect sudden upward movement (negative change) using smoothed value
                if movement < -self.movement_threshold and not self.is_jumping:
                    # Use the potentially modified jump strength
                    self.jump_velocity = current_jump_strength
                    self.is_jumping = True
                    print(f"Jump triggered! Smoothed Movement: {movement:.2f}, Strength: {self.jump_velocity:.2f}") # Debug


                # Update previous smoothed position for the next frame
                self.prev_smoothed_y = smoothed_y
        else:
            # If nose point is lost, clear history and reset smoothing
            self.nose_y_history.clear()
            self.prev_smoothed_y = None

        # Apply gravity and update vertical position
        if self.is_jumping:
            self.rect.y += self.jump_velocity * dt * 60 # Apply dt scaling
            self.jump_velocity += self.gravity * dt * 60 # Apply dt scaling

            # Check if landed
            if self.rect.bottom >= self.ground_level:
                self.rect.bottom = self.ground_level
                self.jump_velocity = 0
                self.is_jumping = False
                print("Landed.") # Debug

    def get_state(self):
        """Return the player's current state (e.g., jumping, position)."""
        return {
            'is_jumping': self.is_jumping,
            'position': self.rect.center,
            'velocity_y': self.jump_velocity
        }
    
    def get_rect(self):
        """Return the player's rectangle."""
        return self.rect

    def reset(self):
        """Reset the player to its initial state."""
        player_config = self.config.get('player', {})
        video_config = self.config.get('video', {})
        
        # Reset position
        self.rect.x = player_config.get('initial_x', 100)
        self.ground_level = video_config.get('height', 720) - player_config.get('ground_offset', 100)
        self.rect.bottom = self.ground_level
        
        # Reset movement state
        self.jump_velocity = 0
        self.is_jumping = False
        
        # Reset input smoothing
        self.nose_y_history.clear()
        self.prev_smoothed_y = None
        
        # Reset image (in case effects were applied, e.g., transparency)
        if hasattr(self, 'original_image'):
            self.image = self.original_image.copy()
        
        print("Player state reset.") # Debug

    # Add this if you implement sprite sheets later
    # def set_animation_state(self, state):
    #    pass # Implement based on improve.md examples 