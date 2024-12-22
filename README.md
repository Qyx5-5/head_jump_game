# Head Jump Game with Face Detection

A Python-based interactive game that uses face detection and head movement tracking for control. Players navigate through obstacles by moving their head up to jump, creating an engaging hands-free gaming experience.

## 🎮 Features

- Real-time face detection and head movement tracking using MediaPipe
- Dynamic obstacle generation with varying types (tall, short, wide)
- Power-up system with score multipliers
- Progressive difficulty scaling
- Score tracking and persistent leaderboard
- Multiple game states (Menu, Playing, Game Over)
- Performance monitoring with FPS display
- Camera feed overlay during gameplay
- Configurable game settings

## 🛠️ Requirements

```python:requirements.txt
opencv-python>=4.5.0
mediapipe>=0.8.0
deepface>=0.0.75
numpy>=1.19.0
fer>=22.4.0
moviepy>=1.0.3
tensorflow>=2.4.0 
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/head-jump-game.git
cd head-jump-game
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎯 Usage

1. Run the game:
```bash
python run.py
```

2. Additional command-line options:
```bash
python run.py --camera 0 --host 127.0.0.1 --port 8000 --detection_confidence 0.5 --config config.json
```

### Game Controls
- **Head Movement**: Move your head up to make the character jump
- **Space**: Start game / Restart after game over
- **ESC**: Return to menu
- **Q**: Quit game
- **S**: Toggle statistics display
- **N**: Enter player name
- **L**: View leaderboard
- **D**: Toggle debug mode

## 🎲 Gameplay

1. **Main Menu**: Press Space to start the game
2. **Playing**: 
   - Use head movements to jump over obstacles
   - Collect power-ups for score multipliers
   - Avoid colliding with obstacles
3. **Game Over**: 
   - View your final score
   - Press Space to play again
   - Press ESC to return to menu

## 🏗️ Project Structure

```
head-jump-game/
├── src/
│   ├── core/
│   │   ├── engine.py      # Game logic and mechanics
│   │   └── renderer.py    # Visual rendering
│   ├── entities/
│   │   └── player.py      # Player entity management
│   ├── processors/
│   │   ├── base_processor.py
│   │   ├── face_processor.py    # Face detection
│   │   └── video_processor.py   # Video capture and processing
│   └── utils/
│       ├── camera_utils.py      # Camera handling
│       └── game_utils.py        # Utility functions
├── requirements.txt
└── run.py                       # Main entry point
```

## ⚙️ Configuration

The game can be configured through command-line arguments or a configuration file. Key configurable parameters include:

- Camera ID
- Detection confidence threshold
- Host and port settings
- Game physics parameters (gravity, jump strength)
- Visual settings (resolution, FPS)

## 🏆 Leaderboard System

The game maintains a persistent leaderboard of top scores. The leaderboard:
- Stores the top 10 scores
- Saves player names and scores
- Automatically updates after each game
- Persists between game sessions

## 🔧 Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Known Issues

- Camera initialization may require retry on some systems
- Face detection sensitivity may vary based on lighting conditions

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers.
