
try:
    import cv2
    print("CV2: OK")
except ImportError:
    print("CV2: MISSING")

try:
    import mediapipe
    print("MEDIAPIPE: OK")
except ImportError:
    print("MEDIAPIPE: MISSING")
