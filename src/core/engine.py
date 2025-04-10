import pygame
import numpy as np
import random
from datetime import datetime
from src.utils.game_utils import GameState
from src.entities.player import Player

class GameEngine:
    def __init__(self, config, asset_manager):
        self.config = config
        self.asset_manager = asset_manager
        self._game_state = GameState.MENU
        self.score = 0
        self.distance_traveled = 0
        self.start_time = None

        # -- Merged from ObstacleManager --
        self.obstacles = []
        self.obstacle_spawn_timer = 0
        game_config = config.get('game', {})
        video_config = config.get('video', {})
        self.base_obstacle_speed = game_config.get('obstacle_speed', 10)
        self.base_min_spawn_interval = game_config.get('min_spawn_interval', 50)
        self.base_max_spawn_interval = game_config.get('max_spawn_interval', 100)
        self.current_obstacle_speed = self.base_obstacle_speed
        self.current_min_spawn_interval = self.base_min_spawn_interval
        self.current_max_spawn_interval = self.base_max_spawn_interval
        self._next_spawn_frame = self._calculate_next_spawn_frame()
        self.pattern_queue = []
        # Load pattern_spawn_chance from difficulty section for consistency
        self.pattern_spawn_chance = config.get('difficulty', {}).get('pattern_spawn_chance', 0.3)
        # Load available_patterns from the top-level config, not game_config
        self.available_patterns = config.get('obstacle_patterns', {
            # Default patterns if not found in config.json
            "double_low": ["low_cactus", "short_gap", "low_cactus"],
            "high_low": ["flying_rock", "wide_gap", "low_cactus"]
        })
        self.obstacle_types = config.get('obstacles', {})
        self.screen_width = video_config.get('width', 1280)
        self.screen_height = video_config.get('height', 720) # Added for consistency
        self.ground_level = self.screen_height - config.get('player', {}).get('ground_offset', 100)
        # -- End ObstacleManager Init --

        # -- Merged from PowerUpManager --
        self.power_ups = []
        self.power_up_active = False # Tracks if *any* powerup is active
        self.active_power_up_type = None # Stores the type of the current active powerup
        self.power_up_timer = None
        self.power_up_duration = config.get('powerup', {}).get('default_duration', 5) # Get default duration
        self.score_multiplier = 1.0
        self.is_invincible = False
        self.slow_motion_factor = 1.0 # 1.0 means normal speed
        # -- End PowerUpManager Init --

        # Initialize sprite groups
        self.all_sprites = pygame.sprite.Group()

        # Create player
        self.player = Player(config, self.asset_manager)
        self.all_sprites.add(self.player)

    def update(self, dt, nose_point=None):
        if self._game_state != GameState.PLAYING:
            return

        if self.start_time is None:
            self.start_time = datetime.now()

        # Update player
        self.player.update(dt, nose_point)

        # --- Integrated Obstacle Update ---
        self._update_difficulty(self.score)
        self.obstacle_spawn_timer += 1
        if self.obstacle_spawn_timer >= self._next_spawn_frame:
            self.obstacle_spawn_timer = 0
            self._spawn_obstacle_or_pattern()
            self._next_spawn_frame = self._calculate_next_spawn_frame()
        self._update_obstacle_positions(dt)
        # --- End Integrated Obstacle Update ---

        # --- Integrated PowerUp Update ---
        self._spawn_powerups()
        self._update_powerup_positions(dt)
        self._check_powerup_duration()
        # --- End Integrated PowerUp Update ---

        # Check for collisions
        self._check_collisions()

        # Update score
        self._update_score(dt) # Pass dt for potential distance calculation refinement

    # --- Merged ObstacleManager Methods ---
    def _calculate_next_spawn_frame(self):
        return random.randint(self.current_min_spawn_interval, self.current_max_spawn_interval)

    def _update_difficulty(self, game_score):
        difficulty_config = self.config.get('difficulty', {})
        speed_increase_interval = difficulty_config.get('speed_increase_score', 500)
        speed_increase_amount = difficulty_config.get('speed_increase_amount', 0.5)
        interval_decrease_interval = difficulty_config.get('interval_decrease_score', 1000)
        interval_decrease_amount = difficulty_config.get('interval_decrease_amount', 3)
        min_interval = difficulty_config.get('min_interval_cap', 25)

        if speed_increase_interval > 0 and game_score > 0:
            score_level_speed = game_score // speed_increase_interval
            self.current_obstacle_speed = self.base_obstacle_speed + score_level_speed * speed_increase_amount

        if interval_decrease_interval > 0 and game_score > 0:
            score_level_interval = game_score // interval_decrease_interval
            reduction = score_level_interval * interval_decrease_amount
            self.current_min_spawn_interval = max(min_interval, self.base_min_spawn_interval - reduction)
            self.current_max_spawn_interval = max(min_interval + 10, self.base_max_spawn_interval - reduction) # Ensure max > min

    def _spawn_obstacle_or_pattern(self):
        if not self.pattern_queue:
            if random.random() < self.pattern_spawn_chance and self.available_patterns:
                self._generate_pattern()
            else:
                valid_types = [t for t in self.obstacle_types.keys() if 'gap' not in t and t != 'base']
                if valid_types:
                    self._create_obstacle(random.choice(valid_types))

        if self.pattern_queue:
            next_item = self.pattern_queue.pop(0)
            if "gap" in next_item:
                gap_frames = self.obstacle_types.get(next_item, {}).get('frames', 10)
                # Adjust spawn timer instead of directly delaying; effectively skips spawn cycles
                self.obstacle_spawn_timer -= gap_frames
                # print(f"Spawning gap ({gap_frames} frames delay)") # Optional debug
            elif next_item != "None": # Handle potential "None" string in pattern
                self._create_obstacle(next_item)

    def _generate_pattern(self):
        if not self.available_patterns:
            return
        pattern_name = random.choice(list(self.available_patterns.keys()))
        self.pattern_queue = list(self.available_patterns[pattern_name])
        # print(f"Generated pattern: {pattern_name} -> {self.pattern_queue}") # Optional debug

    def _create_obstacle(self, obstacle_type):
        type_config = self.obstacle_types.get(obstacle_type)
        if not type_config:
            print(f"Warning: Unknown obstacle type '{obstacle_type}' requested.")
            return

        base_config = self.obstacle_types.get('base', {})
        width = type_config.get('width', base_config.get('width', 50))
        height_min = type_config.get('height_min', base_config.get('height_min', 50))
        height_max = type_config.get('height_max', base_config.get('height_max', 100))
        height = random.randint(height_min, height_max)
        color = tuple(type_config.get('color', base_config.get('color', (255, 0, 0)))) # Ensure color is tuple
        y_pos_type = type_config.get('y_pos', base_config.get('y_pos', 'ground'))
        speed = self.current_obstacle_speed # Use current dynamic speed

        if y_pos_type == 'ground':
            y = self.ground_level - height
        elif y_pos_type == 'air':
             # Ensure air obstacles don't overlap excessively with ground obstacles or go too low/high
            min_air_y = self.ground_level * 0.3 # Example: 30% from top of ground level
            max_air_y = self.ground_level * 0.7 - height # Example: Max 70% from top, accounting for height
            if max_air_y < min_air_y: max_air_y = min_air_y # Prevent invalid range
            y = random.uniform(min_air_y, max_air_y) # Use uniform for float pos if needed
        else: # Default to ground if unknown type
            y = self.ground_level - height

        self.obstacles.append({
            'x': float(self.screen_width), # Start off-screen right
            'y': float(y),
            'width': width,
            'height': height,
            'speed': speed,
            'color': color,
            'type': obstacle_type
        })

    def _update_obstacle_positions(self, dt):
        active_obstacles = []
        # Use speed * dt * 60 for frame-rate independent movement
        # Apply slow motion factor to the current dynamic speed
        effective_speed = self.current_obstacle_speed * self.slow_motion_factor
        move_amount = effective_speed * dt * 60

        # Update powerup speeds if slow motion is active (optional, based on design)
        # Could also adjust powerup speed directly when slow motion activates/deactivates
        powerup_speed_factor = self.config.get('powerup', {}).get('speed_factor', 0.8)
        effective_powerup_speed = effective_speed * powerup_speed_factor

        for obstacle in self.obstacles:
            obstacle['x'] -= move_amount
            # Update obstacle speed attribute if needed by other logic (e.g., scoring)
            obstacle['speed'] = effective_speed
            if obstacle['x'] + obstacle['width'] > 0: # Keep if still visible
                active_obstacles.append(obstacle)
        self.obstacles = active_obstacles

    def get_obstacles(self): # Keep for renderer access
        return self.obstacles
    # --- End ObstacleManager Methods ---

    # --- Merged PowerUpManager Methods ---
    def _spawn_powerups(self):
        powerup_config = self.config.get('powerup', {})
        spawn_chance = powerup_config.get('spawn_chance', 0.001) # Lower default if not specified
        available_types = list(powerup_config.get('types', {}).keys())

        # Don't spawn if no types defined or another powerup is active
        if not available_types or self.power_up_active:
            return

        if random.random() < spawn_chance:
            chosen_type = random.choice(available_types)
            type_config = powerup_config['types'][chosen_type]
            color = tuple(type_config.get('color', (255, 255, 0))) # Default to yellow
            
            # Use current dynamic obstacle speed, modified by powerup speed factor
            base_speed = self.current_obstacle_speed
            speed_factor = powerup_config.get('speed_factor', 0.8)
            powerup_speed = base_speed * speed_factor

            # TODO: Improve y-position randomization?
            y_pos = self.ground_level - random.randint(30, 80)

            self.power_ups.append({
                'x': float(self.screen_width), # Start off-screen right
                'y': float(y_pos),
                'type': chosen_type,
                'width': 20, # Consider making configurable
                'height': 20,
                'speed': powerup_speed,
                'color': color
            })
            print(f"Spawned powerup: {chosen_type}") # Debug

    def _update_powerup_positions(self, dt):
        # Use dt for frame-rate independence if speeds are high or dt varies
        active_powerups = []
        # Apply slow motion factor to powerup speed as well
        effective_speed = self.current_obstacle_speed * self.slow_motion_factor
        powerup_speed_factor = self.config.get('powerup', {}).get('speed_factor', 0.8)
        effective_powerup_speed = effective_speed * powerup_speed_factor
        move_amount = effective_powerup_speed * dt * 60

        for power_up in self.power_ups:
            # Update the speed stored in the powerup dict itself if necessary
            power_up['speed'] = effective_powerup_speed 
            power_up['x'] -= move_amount # Use dt-adjusted move amount
            if power_up['x'] + power_up['width'] > 0:
                active_powerups.append(power_up)
        self.power_ups = active_powerups

    def _check_powerup_duration(self):
        if self.power_up_active and self.power_up_timer:
            if (datetime.now() - self.power_up_timer).total_seconds() > self.power_up_duration:
                self._deactivate_powerup()

    def _handle_powerup_collision(self, power_up):
        # Prevent activating a new powerup if one is already active
        if self.power_up_active:
            return
        
        powerup_config = self.config.get('powerup', {})
        powerup_type = power_up.get('type')
        type_config = powerup_config.get('types', {}).get(powerup_type, {})
        
        print(f"Collided with powerup: {powerup_type}") # Debug
        
        self.power_up_active = True
        self.active_power_up_type = powerup_type
        self.power_up_timer = datetime.now()
        self.power_up_duration = type_config.get('duration', powerup_config.get('default_duration', 5))

        if powerup_type == 'score_boost':
            self.score_multiplier = type_config.get('multiplier', 2.0)
            print(f"Score Boost activated! Multiplier: {self.score_multiplier}, Duration: {self.power_up_duration}s")
        elif powerup_type == 'invincibility':
            self.is_invincible = True
            print(f"Invincibility activated! Duration: {self.power_up_duration}s")
        elif powerup_type == 'slow_motion':
            self.slow_motion_factor = type_config.get('speed_multiplier', 0.5)
            print(f"Slow Motion activated! Factor: {self.slow_motion_factor}, Duration: {self.power_up_duration}s")
        
        # Remove the collected powerup
        try:
             self.power_ups.remove(power_up)
        except ValueError: # Handle case where powerup might already be removed (e.g., race condition)
             print(f"Warning: Could not remove powerup {power_up}, already removed?")
             pass 

    def get_powerups(self): # Keep for renderer access
        return self.power_ups

    def get_score_multiplier(self): # Keep for renderer/UI access
        return self.score_multiplier

    def is_powerup_active(self): # Renamed for clarity
        return self.power_up_active

    def _deactivate_powerup(self):
        print(f"Deactivating powerup: {self.active_power_up_type}") # Debug
        self.power_up_active = False
        self.active_power_up_type = None
        self.score_multiplier = 1.0
        self.is_invincible = False
        self.slow_motion_factor = 1.0
        self.power_up_timer = None
    # --- End PowerUpManager Methods ---

    def get_game_state(self):
        """Get complete game state dictionary"""
        # Access internal attributes directly
        return {
            'state': self._game_state,
            'all_sprites': self.all_sprites,
            'player': self.player.get_state() if self._game_state == GameState.PLAYING else None,
            'obstacles': self.obstacles, # Direct access
            'power_ups': self.power_ups, # Direct access
            'score': self.score,
            'distance_traveled': self.distance_traveled,
            'score_multiplier': self.score_multiplier, # Direct access
            'is_invincible': self.is_invincible,
            'slow_motion_factor': self.slow_motion_factor
        }

    @property
    def game_state(self):
        return self._game_state

    @game_state.setter
    def game_state(self, new_state):
         # Add logic for transitions if needed (e.g., resetting on GAME_OVER -> MENU)
        if self._game_state == GameState.GAME_OVER and new_state == GameState.MENU:
            self.reset() # Reset when going back to menu from game over
        elif self._game_state == GameState.MENU and new_state == GameState.PLAYING:
             if self.start_time is None: # Reset timer only if starting fresh from menu
                 self.start_time = datetime.now()

        self._game_state = new_state

    def _check_collisions(self):
        player_rect = self.player.get_rect()
        player_is_jumping = self.player.is_jumping

        # Check obstacle collisions only if not invincible
        if not self.is_invincible:
            for obstacle in self.obstacles:
                obstacle_type = obstacle.get('type')
                obstacle_config = self.obstacle_types.get(obstacle_type, {})
                y_pos_type = obstacle_config.get('y_pos', 'ground')
                is_air_obstacle = y_pos_type == 'air'

                # Skip collision check for air obstacles if player is on the ground
                if is_air_obstacle and not player_is_jumping:
                    continue

                # Use the existing _check_collision helper method
                if self._check_collision(player_rect, obstacle):
                    print(f"Collision detected with {obstacle_type} obstacle at ({obstacle['x']:.0f}, {obstacle['y']:.0f})")
                    self.game_state = GameState.GAME_OVER
                    return # Exit early on game over
        else:
             # Optional: Add visual feedback for phasing through obstacles
             pass 

        # Check powerup collisions (always check, regardless of invincibility)
        # Iterate over a copy in case of removal during iteration
        for power_up in list(self.power_ups):
            if self._check_collision(player_rect, power_up):
                self._handle_powerup_collision(power_up) # This prevents activating multiple
                break # Stop checking after collecting one powerup

    def _update_score(self, dt): # Added dt parameter back
        # Simple score increment, adjust based on game design
        time_based_score = dt * 10 # Example: Score based on time survived
        distance_based_score = 0 # Can calculate based on player movement or obstacle speed

        # Apply multiplier
        self.score += int((time_based_score + distance_based_score) * self.score_multiplier)

        # Update distance (example, based on constant speed)
        # Consider using player's actual movement if speed varies
        self.distance_traveled += self.current_obstacle_speed * dt * 60

    def _check_collision(self, rect1, rect2):
        """Check collision between player rect and obstacle/powerup dict."""
        # rect1 is player_rect (pygame.Rect)
        player_rect = rect1

        # Ensure rect2 (obstacle/powerup) has the necessary keys
        if not all(k in rect2 for k in ('x', 'y', 'width', 'height')):
             # Optional: More robust error logging
             # print(f"Warning: Collision check skipped for malformed object: {rect2}")
             return False

        # Create a pygame.Rect for the obstacle/powerup
        item_rect = pygame.Rect(rect2['x'], rect2['y'], rect2['width'], rect2['height'])

        return player_rect.colliderect(item_rect)

    def reset(self):
        """Reset the game state, integrating resets from managers"""
        self.score = 0
        self.distance_traveled = 0
        self.start_time = None # Reset start time

        # Reset player state
        self.player.reset()

        # Reset obstacles
        self.obstacles = []
        self.obstacle_spawn_timer = 0
        # Re-read base speeds from config in case it changed? Or assume constant.
        game_config = self.config.get('game', {})
        self.base_obstacle_speed = game_config.get('obstacle_speed', 10)
        self.base_min_spawn_interval = game_config.get('min_spawn_interval', 50)
        self.base_max_spawn_interval = game_config.get('max_spawn_interval', 100)
        self.current_obstacle_speed = self.base_obstacle_speed
        self.current_min_spawn_interval = self.base_min_spawn_interval
        self.current_max_spawn_interval = self.base_max_spawn_interval
        self._next_spawn_frame = self._calculate_next_spawn_frame()
        self.pattern_queue = []

        # Reset powerups
        self.power_ups = []
        self._deactivate_powerup() # Resets all powerup effects/states

        print("Game engine reset.") # Unified reset message