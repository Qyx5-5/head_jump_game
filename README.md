# Head Jump Game

A simple game controlled by head movements via your webcam, using OpenCV and MediaPipe for face detection. Move your head (specifically, your nose) up and down to make the character jump over obstacles.

## Features

*   **Webcam Control:** Play the game using your head movements.
*   **Face Detection:** Utilizes MediaPipe Face Mesh to track your nose position in real-time.
*   **Configurable:** Adjust game physics, video settings, and face detection parameters via `config.json`.
*   **Real-time Statistics:** Displays FPS, camera resolution, detected faces, game state, and score.
*   **Leaderboard:** Tracks high scores (persisted in `leaderboard.json`).
*   **Multiple Camera Support:** Can switch between available cameras.

## Requirements

*   Python 3.7+
*   OpenCV (`opencv-python`)
*   MediaPipe (`mediapipe`)
*   NumPy (`numpy`)
*   (Potentially other dependencies listed in `requirements.txt` - ensure all are installed)

```bash
pip install -r requirements.txt
```

## Installation

1.  **Clone the repository (if applicable):**
    ```bash
    # git clone <repository-url>
    # cd <repository-directory>
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure you have Python and pip installed.*

## Configuration

The game's behavior can be customized by editing the `config.json` file:

```json
{
    "video": {
        "width": 1280,          // Target camera resolution width
        "height": 720,          // Target camera resolution height
        "target_fps": 60,       // Target frames per second
        "camera_id": 0          // Default camera index (can be overridden by command-line)
    },
    "game": {
        "gravity": 2.0,         // Player gravity strength
        "jump_strength": -25,   // Upward velocity applied on jump (negative is up)
        "movement_threshold": 30, // Pixel distance nose needs to move down to trigger jump (needs verification)
        "obstacle_speed": 12,   // How fast obstacles move across the screen
        "min_spawn_interval": 45 // Minimum frames between obstacle spawns
    },
    "player": {
        "initial_x": 100,       // Starting horizontal position of the player
        "size": 50,             // Size of the player character (diameter/width)
        "ground_level_offset": 100 // Distance from bottom edge for the ground
    },
    "powerup": {                // (Powerup logic might not be fully implemented)
        "duration": 5,
        "score_multiplier": 2.0
    },
    "face_detection": {
        "enabled": true,                   // Enable/disable face detection
        "max_faces": 1,                    // Max number of faces to detect
        "refine_landmarks": true,          // Use refined landmarks for better precision (e.g., iris)
        "min_detection_confidence": 0.5,   // Minimum confidence for initial face detection
        "min_tracking_confidence": 0.5,    // Minimum confidence for tracking face across frames
        "process_every_n_frames": 1        // Process face detection every N frames (1 = every frame)
    }
}
```
*Note: Some configurations like `movement_threshold` might need adjustment based on gameplay feel.*
*The face detection confidence values can also be overridden via command-line arguments.*

## How to Run

Execute the main script from your terminal:

```bash
python run.py
```

### Command-Line Arguments

You can override some settings using command-line arguments:

*   `--camera <id>`: Specify the camera index to use (e.g., `--camera 1`). Overrides the `camera_id` in `config.json`.
    *   Example: `python run.py --camera 1`
*   `--detection_confidence <value>`: Set the minimum confidence for face detection (0.0 to 1.0). Overrides the value in `config.json`.
    *   Example: `python run.py --detection_confidence 0.7`
*   `--config <path>`: Specify a different path for the configuration file.
    *   Example: `python run.py --config my_custom_config.json`
*   `--host <ip>`: Set the host address (default: `127.0.0.1`). *Usage may be for future features.*
*   `--port <number>`: Set the port number (default: `8000`). *Usage may be for future features.*

## Controls

*   **Player Movement:** Move your head/nose *down* relative to its starting position to make the character jump. The exact sensitivity might depend on the `movement_threshold` in `config.json`.
*   **Game Control (Keyboard - Common conventions, verify in code if needed):**
    *   `q`: Quit the game.
    *   `r`: Restart the game after game over.
    *   `p`: Pause/Resume the game (potentially).
    *   `c`: Switch to the next available camera (if multiple cameras are detected).
    *   `s`: Toggle the statistics display overlay.
    *   `d`: Toggle debug mode (may show extra info).

*Note: Specific key bindings are handled in `src/core/input_handler.py` - check that file for exact controls.*

## Project Structure

```
.
├── config.json         # Configuration file for game and video settings
├── requirements.txt    # Python dependencies
├── run.py              # Main script to launch the game
├── src/                # Source code directory
│   ├── core/           # Core game logic (engine, renderer, input)
│   ├── processors/     # Video and face processing (video_processor.py)
│   ├── entities/       # Game entities (player, obstacles - potential location)
│   ├── gui/            # Graphical User Interface elements (potential location)
│   └── utils/          # Utility functions (config manager, game state, etc.)
├── assets/             # Game assets (images, sounds - if any)
├── leaderboard.json    # Stores high scores
└── README.md           # This file
```
