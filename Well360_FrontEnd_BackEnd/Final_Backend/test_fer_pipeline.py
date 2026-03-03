"""Quick test of the FER video emotion pipeline."""
import cv2
import sys
import os
import time

sys.path.insert(0, os.path.join("Mental-H", "Emotional"))
from video_preprocessor import enhance_frame, is_frame_blurry

# Load FER
try:
    from fer.fer import FER
except ImportError:
    from fer import FER

print("Creating FER detector...")
detector = FER(mtcnn=True)
print("FER ready.")

# Find a video
video_dir = os.path.join("Mental-H", "Emotional", "savedEmoVideos")
vids = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
if not vids:
    print("No test videos found!")
    sys.exit(1)

vid_path = os.path.join(video_dir, vids[0])
print("Testing:", vid_path)

cap = cv2.VideoCapture(vid_path)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
print("  Frames:", total, "FPS:", fps)

# Test 5 evenly spaced frames
faces_found = 0
for i in range(min(5, total)):
    idx = i * (total // 5) if total > 5 else i
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ret, frame = cap.read()
    if not ret:
        print("  Frame", i, ": read FAILED")
        continue

    blurry = is_frame_blurry(frame, threshold=30.0)
    h, w = frame.shape[:2]
    print("  Frame", i, "idx=", idx, "size=", w, "x", h, "blurry=", blurry)

    if not blurry:
        frame = enhance_frame(frame)
        t0 = time.time()
        results = detector.detect_emotions(frame)
        t1 = time.time()
        elapsed = round(t1 - t0, 2)
        print("    FER:", len(results), "faces in", elapsed, "seconds")
        if results:
            faces_found += 1
            emo = results[0]["emotions"]
            print("    Emotions:", emo)
        else:
            print("    (no faces detected)")

cap.release()
print("\nTotal faces found:", faces_found, "/ 5 tested frames")
