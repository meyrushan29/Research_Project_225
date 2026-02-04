import sys
import os
import cv2
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from fitness.api_handler import get_processor
    print("SUCCESS: Imported get_processor")
except ImportError as e:
    print(f"FAILURE: Could not import get_processor: {e}")
    sys.exit(1)

def create_dummy_video(filename):
    height, width = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
    
    for i in range(30): # 1 second
        frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    print(f"Created dummy video: {filename}")

def test_processor():
    dummy_video = "test_video.mp4"
    create_dummy_video(dummy_video)
    
    try:
        processor = get_processor()
        print("Initialized processor")
        
        result = processor.process_video(dummy_video, output_dir="test_output")
        print("Processing result:", result)
        
        if result.get("success"):
            print("SUCCESS: Video processing completed")
        else:
            print("FAILURE: Video processing returned error")
            
    except Exception as e:
        print(f"CRITICAL FAILURE during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(dummy_video):
            os.remove(dummy_video)

if __name__ == "__main__":
    test_processor()
