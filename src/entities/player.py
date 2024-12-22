class Player:
    def __init__(self, config):
        self.config = config
        self.x = 100
        self.y = self.config.get('height', 720) - 100  # Ground level
        self.size = 50
        self.jump_velocity = 0
        self.gravity = self.config.get('gravity', 2.0)
        self.jump_strength = self.config.get('jump_strength', -25)
        self.is_jumping = False
        self.ground_level = self.config.get('height', 720) - 100
        self.prev_nose_y = None
        self.movement_threshold = self.config.get('movement_threshold', 30)

    def update(self, dt, nose_point=None):
        if nose_point is not None:
            current_y = nose_point[1]
            
            # Initialize previous position if needed
            if self.prev_nose_y is None:
                self.prev_nose_y = current_y
                
            # Calculate movement (negative is upward)
            movement = current_y - self.prev_nose_y
            
            # Detect sudden upward movement
            if movement < -self.movement_threshold and not self.is_jumping:
                self.jump_velocity = self.jump_strength
                self.is_jumping = True
            
            self.prev_nose_y = current_y
        
        # Apply gravity and update player position
        if self.is_jumping:
            self.y += self.jump_velocity
            self.jump_velocity += self.gravity
            
            # Check if landed
            if self.y >= self.ground_level:
                self.y = self.ground_level
                self.jump_velocity = 0
                self.is_jumping = False

    def get_state(self):
        return {
            'x': self.x,
            'y': self.y,
            'size': self.size,
            'ground_level': self.ground_level
        }
    
    def get_rect(self):
        return {
            'x': self.x,
            'y': self.y - self.size,
            'width': self.size,
            'height': self.size
        } 