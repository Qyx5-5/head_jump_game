import cv2

def get_available_cameras(max_cameras=5):
    """Check available camera indices"""
    available = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available 