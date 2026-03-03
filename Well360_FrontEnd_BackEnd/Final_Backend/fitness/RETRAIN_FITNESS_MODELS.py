"""
=============================================================
  WELL360 FITNESS MODEL RETRAINING PIPELINE
  ─────────────────────────────────────────
  Step 1: Extracts pose landmarks from all videos in /dataset/
  Step 2: Trains XGBoost classifier (exercise + form detection)
  Step 3: Saves updated models to /Models/

  Run this file from inside the /fitness/ folder:
      cd Final_Backend/fitness
      python RETRAIN_FITNESS_MODELS.py

=============================================================
"""
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
import os
import warnings
import joblib
import time
import sys

warnings.filterwarnings("ignore")

from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from collections import Counter

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
DATASET_DIR   = "dataset"
CSV_OUTPUT    = "exercise_dataset_with_phase.csv"
MODEL_DIR     = "Models"

# Frame skip: process every Nth frame (speeds up extraction ~3x)
# 2 = skip every other frame, 3 = keep 1 in 3
FRAME_SKIP    = 2

# Resize frames to smaller resolution before pose detection (faster)
# None = keep original, (640, 480) = resize
RESIZE_TO     = (640, 360)

# XGBoost params (balanced speed + accuracy)
XGB_ESTIMATORS  = 400
XGB_MAX_DEPTH   = 8
XGB_LEARNING_RATE = 0.08
XGB_SUBSAMPLE   = 0.85
XGB_COL_SAMPLE  = 0.85

# ─────────────────────────────────────────────────────────
# MediaPipe Setup
# ─────────────────────────────────────────────────────────
mp_pose = mp.solutions.pose

os.makedirs(MODEL_DIR, exist_ok=True)


# =============================================================
# HELPER: EXERCISE NAME NORMALIZER
# =============================================================
def normalize_name(name: str) -> str:
    return name.lower().strip().replace(" ", "_").replace("-", "_")


# =============================================================
# STEP 1: DATASET EXTRACTION
# =============================================================
def extract_landmarks_from_video(video_path: str, exercise_type: str, form_label: int):
    """
    Extracts 132 MediaPipe pose features per valid frame.
    Returns list of rows: [x_0..v_32, exercise_type, label]
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  ❌ Cannot open: {video_path}")
        return []

    data = []
    frame_idx = 0

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.45,
        min_tracking_confidence=0.45,
    )

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1

            # ── Frame skip (speed-up) ──
            if frame_idx % FRAME_SKIP != 0:
                continue

            # ── Resize (speed-up) ──
            if RESIZE_TO:
                frame = cv2.resize(frame, RESIZE_TO)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result.pose_landmarks:
                row = []
                for lm in result.pose_landmarks.landmark:
                    row.extend([lm.x, lm.y, lm.z, lm.visibility])
                row += [exercise_type, form_label]
                data.append(row)
    finally:
        cap.release()
        pose.close()

    return data


def build_dataset():
    """
    Walks dataset/ folder structure:
        dataset/<exercise_name>/correct/*.mp4
        dataset/<exercise_name>/wrong/*.mp4
    Saves CSV incrementally.
    """
    print("\n" + "=" * 60)
    print("  STEP 1: BUILDING DATASET FROM VIDEOS")
    print("=" * 60)

    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset folder not found: {DATASET_DIR}")
        return False

    # Build column names
    columns = []
    for i in range(33):
        columns += [f"x_{i}", f"y_{i}", f"z_{i}", f"v_{i}"]
    columns += ["exercise_type", "label"]

    # Remove old CSV so we start fresh
    if os.path.exists(CSV_OUTPUT):
        os.remove(CSV_OUTPUT)
        print(f"  🗑  Removed old {CSV_OUTPUT}")

    total_videos = 0
    total_rows   = 0
    label_counts = {}

    video_exts = (".mp4", ".avi", ".mov", ".mkv", ".MP4", ".AVI", ".MOV", ".MKV")

    for exercise_folder in sorted(os.listdir(DATASET_DIR)):
        ex_path = os.path.join(DATASET_DIR, exercise_folder)
        if not os.path.isdir(ex_path):
            continue

        exercise_norm = normalize_name(exercise_folder)

        for form_name, form_int in [("correct", 1), ("wrong", 0)]:
            form_path = os.path.join(ex_path, form_name)
            if not os.path.exists(form_path):
                print(f"  ⚠  Missing folder: {form_path}")
                continue

            video_files = [
                f for f in os.listdir(form_path)
                if f.endswith(video_exts)
            ]

            if not video_files:
                print(f"  ⚠  No videos in: {form_path}")
                continue

            print(f"\n  📂 {exercise_norm}/{form_name} ({len(video_files)} videos)")

            for vfile in sorted(video_files):
                vpath = os.path.join(form_path, vfile)
                print(f"     ▶ {vfile}", end="", flush=True)

                rows = extract_landmarks_from_video(vpath, exercise_norm, form_int)

                if rows:
                    df = pd.DataFrame(rows, columns=columns)
                    first_write = not os.path.exists(CSV_OUTPUT)
                    df.to_csv(CSV_OUTPUT, mode="a", header=first_write, index=False)
                    total_rows += len(rows)

                    label_key = f"{exercise_norm}_{form_name}"
                    label_counts[label_key] = label_counts.get(label_key, 0) + len(rows)

                    print(f"  → {len(rows)} frames")
                else:
                    print("  → 0 valid frames")

                total_videos += 1

    print(f"\n{'─' * 50}")
    print(f"  ✅ Extraction Complete")
    print(f"  📹 Videos processed : {total_videos}")
    print(f"  📊 Total rows       : {total_rows:,}")
    print(f"{'─' * 50}")
    print("\n  Class distribution:")
    for k, v in sorted(label_counts.items()):
        print(f"    {k:<40} → {v:>7,} frames")

    return total_rows > 0


# =============================================================
# STEP 2: TRAIN XGBoost MODEL
# =============================================================
def train_model():
    print("\n" + "=" * 60)
    print("  STEP 2: TRAINING XGBoost MODEL")
    print("=" * 60)

    if not os.path.exists(CSV_OUTPUT):
        print(f"❌ CSV not found: {CSV_OUTPUT}")
        return False

    # ── Load Data ──
    print("  📂 Loading dataset ...")
    df = pd.read_csv(CSV_OUTPUT).dropna()
    print(f"  ✅ Loaded: {len(df):,} rows")

    # ── Normalize exercise names ──
    df["exercise_type"] = (
        df["exercise_type"]
        .str.lower()
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # ── Create combined label (exercise_correct / exercise_wrong) ──
    df["combined"] = df["exercise_type"] + "_" + df["label"].map({1: "correct", 0: "wrong"})

    print(f"\n  Classes found: {df['combined'].nunique()}")
    class_counts = df["combined"].value_counts()
    print("  Top 10 classes:")
    print(class_counts.head(10).to_string())

    # Remove very small classes (< 30 frames) — they cause stratify errors
    min_frames = 30
    valid_classes = class_counts[class_counts >= min_frames].index
    removed = df["combined"].nunique() - len(valid_classes)
    if removed > 0:
        print(f"\n  ⚠  Removed {removed} class(es) with < {min_frames} frames")
    df = df[df["combined"].isin(valid_classes)].reset_index(drop=True)
    print(f"  ✅ Remaining: {len(df):,} rows, {df['combined'].nunique()} classes")

    # ── Features & Labels ──
    EXCLUDE = ["exercise_type", "label", "combined"]
    feature_cols = [c for c in df.columns if c not in EXCLUDE]

    X = df[feature_cols].values
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["combined"])

    print(f"\n  Feature count : {len(feature_cols)}")
    print(f"  Total classes : {len(label_encoder.classes_)}")

    # ── Train / Test Split ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,
        random_state=42
    )
    print(f"\n  Train samples : {len(X_train):,}")
    print(f"  Test  samples : {len(X_test):,}")

    # ── Scale ──
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # ── Compute class weights for imbalance ──
    class_freq = Counter(y_train)
    n_total = len(y_train)
    n_classes = len(label_encoder.classes_)
    class_weights = {
        cls: n_total / (n_classes * count)
        for cls, count in class_freq.items()
    }
    sample_weights = np.array([class_weights[yi] for yi in y_train])

    # ── Train XGBoost ──
    print(f"\n  🚀 Training XGBoost ...")
    print(f"     estimators   = {XGB_ESTIMATORS}")
    print(f"     max_depth    = {XGB_MAX_DEPTH}")
    print(f"     learning_rate= {XGB_LEARNING_RATE}")

    model = XGBClassifier(
        objective="multi:softprob",
        num_class=n_classes,
        n_estimators=XGB_ESTIMATORS,
        max_depth=XGB_MAX_DEPTH,
        learning_rate=XGB_LEARNING_RATE,
        subsample=XGB_SUBSAMPLE,
        colsample_bytree=XGB_COL_SAMPLE,
        eval_metric="mlogloss",
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
        # Try GPU first, fall back to CPU
        tree_method="hist",   # "gpu_hist" if CUDA available
        device="cpu",         # Change "cuda" if GPU available
        verbosity=1,
    )

    try:
        model.set_params(device="cuda", tree_method="hist")
        model.fit(
            X_train_s, y_train,
            sample_weight=sample_weights,
            eval_set=[(X_test_s, y_test)],
            verbose=50
        )
        print("  ✅ Trained on GPU (CUDA)")
    except Exception as gpu_err:
        print(f"  ⚠  GPU failed ({gpu_err}), retrying on CPU ...")
        model.set_params(device="cpu", tree_method="hist")
        model.fit(
            X_train_s, y_train,
            sample_weight=sample_weights,
            eval_set=[(X_test_s, y_test)],
            verbose=50
        )
        print("  ✅ Trained on CPU")

    # ── Evaluate ──
    preds = model.predict(X_test_s)
    acc = accuracy_score(y_test, preds)
    print(f"\n  ✅ Test Accuracy: {acc*100:.2f}%")
    print("\n  📊 Classification Report:\n")
    print(classification_report(
        label_encoder.inverse_transform(y_test),
        label_encoder.inverse_transform(preds),
        zero_division=0
    ))

    # ── Save All Artifacts ──
    print(f"\n  💾 Saving models to {MODEL_DIR}/ ...")
    joblib.dump(model,          f"{MODEL_DIR}/exercise_form_detector.pkl")
    joblib.dump(scaler,         f"{MODEL_DIR}/scaler.pkl")
    joblib.dump(label_encoder,  f"{MODEL_DIR}/label_encoder.pkl")
    joblib.dump(feature_cols,   f"{MODEL_DIR}/training_features.pkl")

    # Save class list for quick inspection
    with open(f"{MODEL_DIR}/class_list.txt", "w") as f:
        for cls in label_encoder.classes_:
            f.write(cls + "\n")

    print(f"  ✅ Saved:")
    print(f"      {MODEL_DIR}/exercise_form_detector.pkl")
    print(f"      {MODEL_DIR}/scaler.pkl")
    print(f"      {MODEL_DIR}/label_encoder.pkl")
    print(f"      {MODEL_DIR}/training_features.pkl")
    print(f"      {MODEL_DIR}/class_list.txt")

    return True


# =============================================================
# MAIN PIPELINE
# =============================================================
if __name__ == "__main__":
    start = time.time()

    print("\n" + "=" * 60)
    print("  WELL360 FITNESS MODEL RETRAINING — FULL PIPELINE")
    print("=" * 60)

    # ── Check if CSV already exists ──
    if os.path.exists(CSV_OUTPUT):
        size_mb = os.path.getsize(CSV_OUTPUT) / (1024 * 1024)
        print(f"\n  ⚠  Found existing CSV: {CSV_OUTPUT} ({size_mb:.1f} MB)")
        if "--full" in sys.argv:
            print("  🤖 Auto-confirm: Re-extracting features (--full flag detected)")
            ans = "y"
        else:
            ans = input("  Re-extract from videos? [y/N]: ").strip().lower()
            
        if ans == "y":
            ok = build_dataset()
        else:
            print("  ✅ Skipping extraction, using existing CSV.")
            ok = True
    else:
        ok = build_dataset()

    if not ok:
        print("❌ Dataset build failed. Exiting.")
        exit(1)

    ok2 = train_model()

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    if ok2:
        print(f"  🎉 DONE! Total time: {elapsed/60:.1f} minutes")
        print(f"  New models are in: {MODEL_DIR}/")
        print(f"  Restart backend to load new models.")
    else:
        print(f"  ❌ Training failed.")
    print("=" * 60 + "\n")
