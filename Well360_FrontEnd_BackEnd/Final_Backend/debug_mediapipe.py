
import traceback
try:
    print("Attempting to import mediapipe...")
    import mediapipe as mp
    print(f"MediaPipe version: {mp.__version__}")
    
    try:
        mp_pose = mp.solutions.pose
        print("mp.solutions.pose loaded successfully")
        pose = mp_pose.Pose()
        print("Pose model initialized successfully")
    except Exception as e:
        print("Error accessing mp.solutions.pose:")
        traceback.print_exc()

except ImportError:
    print("Could not import mediapipe")
    traceback.print_exc()
except Exception as e:
    print("General Error:")
    traceback.print_exc()
