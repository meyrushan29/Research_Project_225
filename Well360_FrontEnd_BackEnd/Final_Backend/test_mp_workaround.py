
try:
    print("Testing MediaPipe workaround...")
    import mediapipe.python.solutions as mp_solutions
    mp_pose = mp_solutions.pose
    print("SUCCESS: mediapipe.python.solutions works.")
except ImportError:
    print("FAILURE: mediapipe.python.solutions not found.")
except Exception as e:
    print(f"FAILURE: {e}")
