import cv2
import numpy as np
from datetime import datetime
import time
import json
import mediapipe as mp

from src.core.engine import GameEngine
from src.core.renderer import Renderer
from src.utils.game_utils import GameState, LeaderboardManager
from src.core.input_handler import InputHandler
from src.utils.config_manager import ConfigManager
from src.utils.asset_manager import AssetManager

def _get_available_cameras(max_cameras=5):
    """Check available camera indices (now a static/module-level function or make it a method)"""
    available = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

class VideoProcessor:
    def __init__(
        self,
        host=None,
        port=None,
        camera_id=0,
        detection_confidence=0.5,
        config_path='config.json',
        cap_device=0,
        args=None
    ):
        self.host = host
        self.port = port
        self.camera_id = camera_id
        self.args = args
        self.cap = None
        self.out = None
        self.stats_enabled = True
        self.fps = 0
        self.start_time = time.time()
        self.frame_count = 0
        self.debug_mode = False

        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        if not self.config_manager.validate_config():
             print("Warning: Config validation failed, using validated defaults where possible.")

        self.asset_manager = AssetManager(self.config)

        self.camera_id = self.config.get('video', {}).get('camera_id', camera_id)

        self.game_engine = GameEngine(self.config, self.asset_manager)
        self.renderer = Renderer(self.config, self.asset_manager)
        self.leaderboard = LeaderboardManager()
        self.input_handler = InputHandler(self.game_engine, self.renderer, self.leaderboard)

        self.face_detection_enabled = self.config.get('face_detection', {}).get('enabled', True)
        self.mp_face_mesh = None
        self.face_mesh = None
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
        self.current_face_count = 0
        self._current_landmarks = None

        if self.face_detection_enabled:
            self._initialize_face_processing(args)
        else:
            print("Face detection disabled in config.")

        self.current_camera = self.camera_id
        self.available_cameras = _get_available_cameras()

        self.process_every_n_frames = getattr(args, 'process_every_n_frames', self.config.get('video', {}).get('process_every_n_frames', 1))
        if self.process_every_n_frames < 1:
            print("Warning: process_every_n_frames must be 1 or greater. Setting to 1.")
            self.process_every_n_frames = 1
        self.frame_counter_for_detection = 0
        self.last_known_nose_point = None

        self.target_resolution = (
            self.config.get('video', {}).get('width', 1280),
            self.config.get('video', {}).get('height', 720)
        )

        print(f"VideoProcessor initialized. Process every {self.process_every_n_frames} frames.")
        print(f"Target resolution: {self.target_resolution}")
        if not self.available_cameras:
            print("Warning: No cameras detected by OpenCV.")
        else:
            print(f"Available cameras: {self.available_cameras}")

    def _initialize_face_processing(self, args):
        """Initializes MediaPipe Face Mesh based on config and args."""
        try:
            self.mp_face_mesh = mp.solutions.face_mesh

            min_det_conf = getattr(args, 'detection_confidence', self.config.get('face_detection', {}).get('min_detection_confidence', 0.5))
            min_track_conf = getattr(args, 'tracking_confidence', self.config.get('face_detection', {}).get('min_tracking_confidence', 0.5))

            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=self.config.get('face_detection', {}).get('max_faces', 1),
                refine_landmarks=self.config.get('face_detection', {}).get('refine_landmarks', True),
                min_detection_confidence=min_det_conf,
                min_tracking_confidence=min_track_conf
            )
            print(f"MediaPipe Face Mesh initialized with det_conf={min_det_conf}, track_conf={min_track_conf}")
        except Exception as e:
            print(f"Warning: MediaPipe Face Mesh initialization failed: {e}")
            self.face_detection_enabled = False

    def draw_stats(self, frame):
        """Draw statistics and information overlay on the frame"""
        self.frame_count += 1
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        if elapsed_time >= 1.0:
            self.fps = self.frame_count / elapsed_time
            self.start_time = current_time
            self.frame_count = 0

        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = 35
        w, h = frame.shape[1], frame.shape[0]
        face_count = self.current_face_count

        stats_lines = [
            f"FPS: {self.fps:.1f}",
            f"Res: {w}x{h}",
            f"Cam: {self.current_camera}",
            f"Faces: {face_count}",
            f"State: {self.game_engine.game_state.value}",
            f"Score: {self.game_engine.score}",
        ]

        box_h = len(stats_lines) * 25 + 10
        # Create an overlay for the transparent rectangle
        overlay = frame.copy()
        # Draw the rectangle on the overlay
        cv2.rectangle(overlay, (10, 10), (200, 10 + box_h), (0, 0, 0), -1)
        # Blend the overlay with the original frame
        alpha = 0.6
        blended_frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        for i, stat in enumerate(stats_lines):
            # Draw text on the blended frame
            cv2.putText(blended_frame, stat, (20, y_offset + i*25),
                       font, 0.5, (255, 255, 255), 1)

        return blended_frame

    def _process_face_frame(self, frame):
        """Process frame for face landmarks and draw nose point."""
        self.current_face_count = 0
        self._current_landmarks = None
        nose_point_detected = None

        if not self.face_detection_enabled or self.face_mesh is None:
            return frame, None

        if frame is None or frame.size == 0:
            print("Warning: Empty frame received in face processor")
            return frame, None

        try:
            if not frame.flags.writeable:
                frame = frame.copy()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False

            results = self.face_mesh.process(rgb_frame)
            rgb_frame.flags.writeable = True

            frame.flags.writeable = True

            if results is not None and results.multi_face_landmarks:
                self.current_face_count = len(results.multi_face_landmarks)
                primary_face_landmarks = results.multi_face_landmarks[0]
                self._current_landmarks = primary_face_landmarks

                h, w = frame.shape[:2]

                try:
                    nose_landmark = primary_face_landmarks.landmark[1]
                    nose_x = int(nose_landmark.x * w)
                    nose_y = int(nose_landmark.y * h)
                    nose_point_detected = (nose_x, nose_y)

                    cv2.circle(frame, nose_point_detected, 5, (0, 255, 0), -1)

                except (IndexError, AttributeError, TypeError) as e:
                    print(f"Error accessing primary nose landmark: {e}")

                return frame, nose_point_detected

        except cv2.error as cv_err:
            print(f"OpenCV error during face processing: {cv_err}")
            return frame, None
        except Exception as e:
            print(f"Critical error in face processing: {type(e).__name__}: {e}")
            return frame, None

    def _get_current_landmarks(self):
        """Return the most recent face landmarks detected."""
        return self._current_landmarks

    def _get_face_stats(self):
        """Return current face processing statistics (just count for now)."""
        return {'face_count': self.current_face_count}

    def process_frame(self, frame):
        """
        Processes a single video frame: face detection, game update, rendering.
        """
        try:
            current_fps = self.fps if self.fps > 0 else self.config.get('video', {}).get('target_fps', 60)
            dt = 1.0 / current_fps

            processed_display_frame = frame
            current_nose_point = self.last_known_nose_point

            if frame is not None and frame.size > 0 and self.face_detection_enabled:
                self.frame_counter_for_detection += 1
                if self.frame_counter_for_detection >= self.process_every_n_frames:
                    self.frame_counter_for_detection = 0

                    # Process face and handle return value robustly
                    face_result = self._process_face_frame(frame)
                    if isinstance(face_result, tuple) and len(face_result) == 2:
                        processed_face_frame, nose_point_detected = face_result
                    else:
                        # Fallback if return value is unexpected
                        print(f"Warning: Unexpected return from _process_face_frame: {face_result}")
                        processed_face_frame = frame 
                        nose_point_detected = None 

                    # Use the processed frame for display
                    processed_display_frame = processed_face_frame
                    
                    # Update current nose point if detected
                    if nose_point_detected is not None:
                        current_nose_point = nose_point_detected
                        self.last_known_nose_point = nose_point_detected
                    # If not detected, current_nose_point retains its value (last_known_nose_point)

                else:
                    # Use last known point if skipping detection frame
                    processed_display_frame = frame # Start with the current camera frame
                    if self.last_known_nose_point and processed_display_frame is not None:
                         # Draw the last known point (make frame writable if needed)
                         if not processed_display_frame.flags.writeable:
                             processed_display_frame = processed_display_frame.copy()
                         cv2.circle(processed_display_frame, self.last_known_nose_point, 5, (255, 0, 0), -1) # Draw red circle for last known
            else:
                 # Handle case where frame is None or face detection disabled
                 processed_display_frame = frame if frame is not None else np.zeros((self.target_resolution[1], self.target_resolution[0], 3), dtype=np.uint8)
                 current_nose_point = None # No face detection, no nose point
                 self.last_known_nose_point = None

            if self.game_engine.game_state == GameState.PLAYING:
                # Pass the determined current_nose_point (could be new, last known, or None)
                self.game_engine.update(dt, current_nose_point)

            game_state_dict = self.game_engine.get_game_state()

            game_surface_cv2 = self.renderer.render(processed_display_frame, game_state_dict)

            if self.stats_enabled:
                 final_frame = self.draw_stats(game_surface_cv2)
            else:
                 final_frame = game_surface_cv2

            return final_frame

        except Exception as e:
            print(f"Error processing frame: {e}")
            if frame is not None:
                 return frame
            else:
                 h = self.config.get('video', {}).get('height', 720)
                 w = self.config.get('video', {}).get('width', 1280)
                 return np.zeros((h, w, 3), dtype=np.uint8)

    def _setup_camera(self):
        """Initializes or re-initializes the camera capture."""
        if self.cap:
            self.cap.release()

        print(f"Attempting to initialize camera ID: {self.current_camera}")
        self.cap = cv2.VideoCapture(self.current_camera)

        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.current_camera}.")
            if self.available_cameras:
                print("Attempting fallback cameras...")
                for cam_id in self.available_cameras:
                    if cam_id != self.current_camera:
                        self.cap = cv2.VideoCapture(cam_id)
                        if self.cap.isOpened():
                            print(f"Successfully opened fallback camera {cam_id}")
                            self.current_camera = cam_id
                            break
                if not self.cap.isOpened():
                     print("Error: Failed to open any available camera.")
                     return False
            else:
                print("Error: No cameras detected.")
                return False

        target_w = self.config.get('video', {}).get('width')
        target_h = self.config.get('video', {}).get('height')
        if target_w and target_h:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_h)
            print(f"Set camera {self.current_camera} resolution to {target_w}x{target_h}")

        target_fps = self.config.get('video', {}).get('target_fps')
        if target_fps:
            self.cap.set(cv2.CAP_PROP_FPS, target_fps)
            print(f"Requested camera {self.current_camera} FPS: {target_fps}")

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Actual camera {self.current_camera} settings: {actual_w}x{actual_h} @ {actual_fps:.2f} FPS")

        self.target_resolution = (actual_w, actual_h)

        return True

    def run(self):
        """Main loop to capture, process, and display video frames."""
        if not self._setup_camera():
             print("Exiting due to camera initialization failure.")
             return

        frame_delay = 1 / self.config.get('video', {}).get('target_fps', 60)

        while True:
            loop_start_time = time.time()

            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("Error reading frame or end of stream.")
                time.sleep(1)
                if not self._setup_camera():
                    print("Failed to re-initialize camera. Exiting.")
                    break
                continue

            processed_frame = self.process_frame(frame)

            cv2.imshow('Head Jump Game', processed_frame)

            key = cv2.waitKey(1)
            if not self.input_handler.handle_input(key):
                break

            loop_end_time = time.time()
            elapsed = loop_end_time - loop_start_time
            wait_time = frame_delay - elapsed
            if wait_time > 0:
                time.sleep(wait_time)

        self.release()

    def release(self):
        """Release resources."""
        if self.cap:
            self.cap.release()
            print("Camera released.")
        if self.out:
            self.out.release()
            print("Video writer released.")
        cv2.destroyAllWindows()
        print("Windows destroyed.")

    def _change_camera(self, direction=1):
        """Change to the next/previous available camera."""
        if not self.available_cameras:
            print("No other cameras available.")
            return

        current_index = -1
        try:
            current_index = self.available_cameras.index(self.current_camera)
        except ValueError:
             current_index = 0

        new_index = (current_index + direction) % len(self.available_cameras)
        new_camera_id = self.available_cameras[new_index]

        if new_camera_id != self.current_camera:
            print(f"Attempting to switch camera to ID: {new_camera_id}")
            self.current_camera = new_camera_id
            if not self._setup_camera():
                 print(f"Failed to switch to camera {new_camera_id}.")
            else:
                 pass
        else:
            print("Already using the only available camera.")