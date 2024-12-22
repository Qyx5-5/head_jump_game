import cv2
import numpy as np
from datetime import datetime
from ..utils.camera_utils import get_available_cameras
from .face_processor import FaceProcessor
from ..core.engine import GameEngine
from ..core.renderer import Renderer
from ..utils.game_utils import GameState, LeaderboardManager
from ..core.input_handler import InputHandler
import json

class VideoProcessor:
    def __init__(
        self,
        host=None,
        port=None,
        camera_id=0,
        detection_confidence=0.5
    ):
        self.host = host
        self.port = port
        self.camera_id = camera_id
        self.cap = None  # Initialize as None
        self.detection_confidence = detection_confidence
            
        try:
            self.face_processor = FaceProcessor()
            self.face_processor.detection_enabled = True
        except Exception as e:
            print(f"Warning: Face processor initialization failed: {str(e)}")
            self.face_processor = None
        
        # States
        
        
        # Video writer
        self.out = None
        self.current_camera = self.camera_id
        self.available_cameras = get_available_cameras()
        
        self.fps = 0
        self.frame_count = 0
        self.start_time = datetime.now()
        self.stats_enabled = True
        
        # High-res settings
        self.resolutions = [
            (3840, 2160),  # 4K
            (2560, 1440),  # 2K
            (1920, 1080),  # 1080p
            (1280, 720)    # 720p
        ]
        self.current_resolution_index = 0
        
        # Performance monitoring
        self.process_every_n_frames = 3  # Process fewer frames
        self.frame_counter = 0
        self.last_nose_point = None
        
        # Increase resolution for better visibility
        self.target_resolution = (1280, 720)
        # Movement smoothing
        self.nose_positions = []
        self.smooth_window = 2  # Reduced from 3
        
        # Debug mode (for development)
        self.debug_mode = False  # New flag for debug info
        
        # Load config
        self.config = self._load_config()
        
        self.game_engine = GameEngine(self.config)
        self.renderer = Renderer(self.config)
        self.leaderboard = LeaderboardManager()
        self.input_handler = InputHandler(self.game_engine, self.renderer, self.leaderboard)
    
    def _load_config(self, config_path="config.json"):
        """Load configuration using ConfigManager"""
        from ..utils.config_manager import ConfigManager
        config_manager = ConfigManager(config_path)
        if not config_manager.validate_config():
            print("Warning: Config validation failed, using validated defaults")
        return config_manager.config
    
    def draw_stats(self, frame):
        """Draw statistics and information overlay on the frame"""
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay for stats
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Calculate FPS
        self.frame_count += 1
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        if elapsed_time > 0:
            self.fps = self.frame_count / elapsed_time
        
        # Get face processor stats
        face_stats = self.face_processor.get_stats()
        
        # Draw stats
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = 35
        stats = [
            f"FPS: {self.fps:.1f}",
            f"Resolution: {w}x{h}",
            f"Camera ID: {self.current_camera}",
            f"Faces Detected: {face_stats['face_count']}",
        ]
        
        for i, stat in enumerate(stats):
            cv2.putText(frame, stat, (20, y_offset + i*25),
                       font, 0.6, (255, 255, 255), 1)
        
        # Draw controls help
        controls = [
            "Q: Quit",
            "S: Toggle Stats",
        ]
        
        # Draw controls in bottom-right corner
        for i, control in enumerate(controls):
            cv2.putText(frame, control, 
                       (w - 150, h - 120 + i*20),
                       font, 0.5, (255, 255, 255), 1)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (w - 190, 30),
                   font, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def _get_nose_position(self, face_landmarks, frame_shape):
        """Extract nose position from face landmarks"""
        if face_landmarks is None:
            return None
        
        # If we received a tuple (x,y), use it directly
        if isinstance(face_landmarks, tuple) and len(face_landmarks) == 2:
            return face_landmarks
        
        # If we have MediaPipe face landmarks
        if hasattr(face_landmarks, 'landmark'):
            # MediaPipe face mesh nose tip index is 1
            nose_landmark = face_landmarks.landmark[1]
            frame_height, frame_width = frame_shape[:2]
            
            # Convert normalized coordinates to pixel coordinates
            nose_x = int(nose_landmark.x * frame_width)
            nose_y = int(nose_landmark.y * frame_height)
            
            return (nose_x, nose_y)
        
        return None  # Invalid input type
    
    def process_frame(self, frame):
        try:
            # Create a blank canvas for the game
            game_canvas = np.zeros((self.config['height'], self.config['width'], 3), dtype=np.uint8)
            
            # Process face detection only if we have a valid frame
            if frame is not None and frame.size > 0:
                if self.face_processor:
                    try:
                        face_frame = self.face_processor.process_frame(frame)
                        landmarks = self.face_processor.get_face_landmarks()
                    except cv2.error as cv_err:
                        print(f"OpenCV error during face processing: {cv_err}")
                        face_frame = frame
                        landmarks = None
                    except Exception as e:
                        print(f"Face processing error: {e}")
                        face_frame = frame
                        landmarks = None
                else:
                    face_frame = frame
                    landmarks = None

                # Get nose position with error handling
                try:
                    nose_point = self._get_nose_position(landmarks, frame.shape)
                except Exception as e:
                    print(f"Error getting nose position: {e}")
                    nose_point = None
                
                # Update game engine only if we have valid nose point
                if self.game_engine.game_state == GameState.PLAYING:
                    self.game_engine.update(1 / max(self.fps, 1), nose_point)
            else:
                face_frame = None
                
            # Get game state
            game_state = self.game_engine.get_game_state()
            
            # Render game with camera feed in corner (if available)
            rendered_frame = self.renderer.render(face_frame, game_state)
            
            if rendered_frame is None:
                print("Warning: Renderer returned None")
                return game_canvas
            
            return rendered_frame
            
        except Exception as e:
            print(f"Critical error in process_frame: {e}")
            # Return a basic error frame
            error_frame = np.zeros((self.config['height'], self.config['width'], 3), dtype=np.uint8)
            cv2.putText(error_frame, f"Processing Error: {str(e)}", 
                        (50, error_frame.shape[0]//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return error_frame
    
    def _draw_minimal_stats(self, frame):
        """Draw minimal stats for better performance"""
        h, w = frame.shape[:2]
        
        # Calculate FPS
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        if elapsed_time > 0:
            self.fps = self.frame_count / elapsed_time
        
        # Draw only essential stats
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (20, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    def _setup_camera(self):
        """Configure camera with highest supported resolution"""
        cap = cv2.VideoCapture(self.camera_id)
        
        # Try setting highest resolution
        for width, height in self.resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            # Try to set 60 FPS
            cap.set(cv2.CAP_PROP_FPS, 60)
            
            # Check if settings were accepted
            actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            
            if actual_width == width and actual_height == height:
                print(f"Camera configured at {width}x{height} @ {actual_fps}fps")
                break
        
        return cap

    def initialize_camera(self):
        """Initialize camera with fallback options"""
        if self.cap is not None:
            self.cap.release()
        
        # Try primary camera
        self.cap = cv2.VideoCapture(self.camera_id)
        if self.cap.isOpened():
            print(f"Camera {self.camera_id} opened successfully")
            return True

        # Try backup camera indices
        for i in range(5):
            if i == self.camera_id:
                continue
            
            if self.cap is not None:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(i)
            if self.cap.isOpened():
                self.camera_id = i
                print(f"Camera {self.camera_id} opened successfully")
                return True
        
        print("Error: Could not initialize any camera")
        return False

    def run(self):
        """Main processing loop"""
        if not self.initialize_camera():
            return False  # Camera initialization failed
            
        self.start_time = datetime.now()
        self.frame_count = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            try:
                processed_frame = self.process_frame(frame)
                if processed_frame is not None and processed_frame.shape[0] > 0 and processed_frame.shape[1] > 0:
                    cv2.imshow('Video Stream', processed_frame)
                else:
                    print("Processed frame is empty")
                    break
            except Exception as e:
                print(f"Error processing frame: {str(e)}")
                break

            # Handle input
            key = cv2.waitKey(1)
            if not self.input_handler.handle_input(key):
                break

        print("Cleaning up...")
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()