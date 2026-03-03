"""
Preprocess Lip Dataset — MediaPipe Lip Crop + Center Crop Fallback
==================================================================
Strategy:
 1. Try MediaPipe FaceMesh to find lip landmarks → tight crop to lip only
 2. Fallback: center-vertical strip crop (middle 70% width, lower 65% height)
    This removes most background while keeping lip tissue intact.

We do NOT use color segmentation — unreliable across different skin tones.

Usage:
    cd d:\\PP2\\Research_Project_225\\Well360_FrontEnd_BackEnd\\Final_Backend
    python hydration/scripts/preprocess_all_lips.py
"""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import cv2
import numpy as np
from tqdm import tqdm

# MediaPipe outer lip indices
LIP_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,
             409, 270, 269, 267, 0, 37, 39, 40, 185]


def crop_lip_mediapipe(img_bgr):
    """
    Detect lip with MediaPipe FaceMesh and crop.
    Returns (crop, True) or (None, False).
    """
    try:
        import mediapipe as mp
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.3
        )
        res = face_mesh.process(img_rgb)
        face_mesh.close()

        if not res.multi_face_landmarks:
            return None, False

        lm = res.multi_face_landmarks[0]
        pts = np.array([(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h))
                        for i in LIP_OUTER], dtype=np.int32)
        x, y, bw, bh = cv2.boundingRect(pts)

        # 8% padding
        px, py = max(4, int(bw * 0.08)), max(4, int(bh * 0.08))
        x1 = max(0, x - px);  y1 = max(0, y - py)
        x2 = min(w, x + bw + px); y2 = min(h, y + bh + py)

        crop = img_bgr[y1:y2, x1:x2]
        if crop.shape[0] < 15 or crop.shape[1] < 20:
            return None, False
        return crop, True
    except Exception:
        return None, False


def crop_center_fallback(img_bgr):
    """
    Center-strip crop: keep middle 70% width, lower 65% height.
    Removes most surrounding background while keeping lip region.
    """
    h, w = img_bgr.shape[:2]
    # Horizontal: center 70%
    cx = int(w * 0.15)  # 15% margin each side
    # Vertical: lower 65% (lips are not at the very top)
    cy = int(h * 0.15)  # cut top 15%
    crop = img_bgr[cy:h, cx:w - cx]
    return crop


def preprocess_dataset(input_dir, output_dir):
    classes = ["Dehydrate", "Normal"]
    total_mp, total_fb = 0, 0

    for cls in classes:
        in_path  = os.path.join(input_dir, cls)
        out_path = os.path.join(output_dir, cls)
        os.makedirs(out_path, exist_ok=True)

        if not os.path.exists(in_path):
            print(f"[SKIP] {in_path}"); continue

        print(f"\n--- {cls} ---")
        files = [f for f in os.listdir(in_path)
                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        mp_ok = 0; fb_ok = 0

        for fn in tqdm(files, desc=f"  {cls}"):
            img = cv2.imread(os.path.join(in_path, fn))
            if img is None: continue

            crop, ok = crop_lip_mediapipe(img)
            if ok:
                mp_ok += 1
            else:
                crop = crop_center_fallback(img)
                fb_ok += 1

            # Resize to 224×224
            crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_LANCZOS4)
            save = os.path.splitext(fn)[0] + ".png"
            cv2.imwrite(os.path.join(out_path, save), crop)

        total_mp += mp_ok; total_fb += fb_ok
        print(f"  MediaPipe: {mp_ok}  |  Center-crop fallback: {fb_ok}")

    print(f"\n{'='*50}")
    print(f"TOTAL  MediaPipe: {total_mp}  |  Fallback: {total_fb}")
    print(f"{'='*50}")


if __name__ == "__main__":
    BASE  = os.path.dirname(os.path.abspath(__file__))
    PAR   = os.path.dirname(BASE)
    print("=" * 60)
    print("  LIP CROP PREPROCESSING")
    print("  Method: MediaPipe FaceMesh → center-crop fallback")
    print("=" * 60)
    preprocess_dataset(
        os.path.join(PAR, "data"),
        os.path.join(PAR, "data_processed")
    )
    print("\nDone. Run: python hydration/training/train_lip_model_complete.py")
