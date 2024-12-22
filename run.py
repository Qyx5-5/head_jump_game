import argparse
from src.processors.video_processor import VideoProcessor

def main():
    parser = argparse.ArgumentParser(description="Run the video processor with optional configurations.")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--camera", type=int, default=0, help="Camera ID")
    parser.add_argument("--detection_confidence", type=float, default=0.5, help="Face detection confidence")
    parser.add_argument("--config", type=str, default="config.json", help="Path to configuration file")

    args = parser.parse_args()

    processor = VideoProcessor(
        host=args.host,
        port=args.port,
        camera_id=args.camera,
        detection_confidence=args.detection_confidence
    )
    processor.run()

if __name__ == "__main__":
    main() 