import cv2
import mediapipe as mp
from .base_processor import BaseProcessor
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Layer
from ..utils.game_utils import GameState

# Handle optional imports
try:
    from fer import FER
except ImportError:
    FER = None
    print("Warning: FER package is not installed. Emotion detection using FER will be unavailable.")

try:
    from moviepy import editor
except ImportError:
    editor = None
    print("Warning: moviepy.editor is not installed. Some video processing features may be unavailable.")

class FaceProcessor(BaseProcessor):
    def __init__(self):
        self.mp_face = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_draw = mp.solutions.drawing_utils

        self.drawing_spec = self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=1)

        # Initialize mediapipe detection
        self.face_detection = self.mp_face.FaceDetection(min_detection_confidence=0.5)
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=3,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # States
        self.detection_enabled = True

        # Stats tracking
        self.current_face_count = 0
        self._current_landmarks = None

    def process_frame(self, frame):
        """Process frame for face detection and draw just a nose point."""
        if not self.detection_enabled:
            return frame

        try:
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Run face landmark detection
            results = self.face_mesh.process(rgb_frame)
            self._current_landmarks = None

            if results is not None and results.multi_face_landmarks:
                self.current_face_count = len(results.multi_face_landmarks)
                # Take the first face as the "primary" face
                self._current_landmarks = results.multi_face_landmarks[0]

                h, w = frame.shape[:2]

                # Draw a single point on the nose for each detected face
                for face_landmarks in results.multi_face_landmarks:
                    nose = face_landmarks.landmark[1]  # Index 1 is typically nose tip in MediaPipe
                    nose_x = int(nose.x * w)
                    nose_y = int(nose.y * h)
                    cv2.circle(frame, (nose_x, nose_y), 5, (0, 255, 0), -1)

            else:
                self.current_face_count = 0

            return frame

        except Exception as e:
            print(f"Warning: Face processing error: {e}")
            return frame

    def get_face_landmarks(self):
        """Return the most recent face landmarks detected."""
        return self._current_landmarks

    def get_stats(self):
        """Return current processing statistics."""
        return {
            'face_count': self.current_face_count,
        }