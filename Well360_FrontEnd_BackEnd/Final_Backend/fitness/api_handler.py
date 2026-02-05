import cv2
import joblib
import mediapipe as mp
import numpy as np
import os
import time
import uuid
import xgboost as xgb
from collections import deque
from pathlib import Path

# Fix paths to be relative to THIS file
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "Models"

# Add parent directory to path to allow imports from fitness/
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from .exercise_config import EXERCISE_CONFIG, COLORS
    from .heatmap import HeatmapVisualizer
    from .geometry import calculate_angles_from_landmarks
    from .utils import (
        create_compact_info_panel,
        draw_progress_bar,
        extract_features,
        create_feature_dataframe,
        load_recommendations,
        save_detailed_report_with_recommendations
    )
except ImportError:
    # Fallback for direct execution/testing
    from exercise_config import EXERCISE_CONFIG, COLORS
    from heatmap import HeatmapVisualizer
    from geometry import calculate_angles_from_landmarks
    from utils import (
        create_compact_info_panel,
        draw_progress_bar,
        extract_features,
        create_feature_dataframe,
        load_recommendations,
        save_detailed_report_with_recommendations
    )

mp_pose = None
mp_draw = None
try:
    # MediaPipe's classic API is `mediapipe.solutions.*`.
    # Some environments accidentally install a different/dist-only `mediapipe` package
    # (or a partial install) that lacks `solutions`. In that case we disable fitness
    # processing rather than crashing the entire backend at import-time.
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
        mp_pose = mp.solutions.pose
        mp_draw = mp.solutions.drawing_utils
    else:
        raise ImportError(
            "MediaPipe 'solutions' API not available (missing mediapipe.solutions.pose)."
        )
except Exception as e:
    print(f"WARNING: {e} Fitness features disabled.")
    mp_pose = None
    mp_draw = None

class FitnessVideoProcessor:
    def __init__(self):
        print(f"--> Loading Fitness Models from {MODELS_DIR}")

        if mp_pose is None:
            raise RuntimeError(
                "Fitness processor cannot start: MediaPipe Pose is unavailable. "
                "Reinstall the official 'mediapipe' package compatible with your Python version."
            )
        
        # Load models using absolute paths
        self.model = joblib.load(MODELS_DIR / "exercise_form_detector.pkl")
        
        # FIX: Handle XGBoost version incompatibility (older pickle vs newer lib)
        if hasattr(self.model, "callbacks") is False:
            self.model.callbacks = []
        if hasattr(self.model, "early_stopping_rounds") is False:
            self.model.early_stopping_rounds = None

        self.scaler = joblib.load(MODELS_DIR / "scaler.pkl")
        self.label_encoder = joblib.load(MODELS_DIR / "label_encoder.pkl")
        self.expected_features = joblib.load(MODELS_DIR / "training_features.pkl")
        print(f"DEBUG: Loaded {len(self.expected_features)} expected features.")
        print(f"DEBUG: First 5 expected features: {self.expected_features[:5]}")

        self.recommendations_file = BASE_DIR / "recommendations.json"

        if mp_pose:
            self.pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.pose = None
            print("DEBUG: MediaPipe Pose failed to initialize.")

        self.heatmap_viz = HeatmapVisualizer()
        self.reset_state()

    def reset_state(self):
        self.prediction_history = deque(maxlen=15)
        self.confidence_history = deque(maxlen=15)
        self.reps = 0
        self.stage = "up"
        self.last_rep_time = 0
        self.MIN_REP_TIME = 0.8
        self.hold_time = 0
        self.hold_start = None
        self.current_exercise = "unknown"
        self.current_form = "unknown"
        self.exercise_counts = {}
        self.form_counts = {"correct": 0, "wrong": 0, "unknown": 0}
        self.predictions = []
        self.no_pose_frames = 0
        self.frame_count = 0

    def update_reps(self, landmarks, exercise):
        # ... (unchanged)
        if exercise not in EXERCISE_CONFIG:
            return

        cfg = EXERCISE_CONFIG[exercise]

        if cfg["type"] == "hold":
            if self.hold_start is None:
                self.hold_start = time.time()
            self.hold_time = int(time.time() - self.hold_start)
            return

        angles = calculate_angles_from_landmarks(landmarks, cfg)
        if "main" not in angles:
            return

        angle = angles["main"]

        # LOGIC: Start UP -> go DOWN -> return UP (Count)
        if angle > cfg["down"]: # Extended / Standing
            if self.stage == "down":
                 now = time.time()
                 if now - self.last_rep_time > self.MIN_REP_TIME:
                     self.reps += 1
                     self.last_rep_time = now
            self.stage = "up"

        if angle < cfg["up"]: # Flexed / Squatting
            self.stage = "down"

    def predict_exercise_and_form(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.pose is None:
            print("DEBUG: Pose model not loaded.")
            return "unknown", "unknown", frame, 0.0, None

        results = self.pose.process(rgb)

        if not results.pose_landmarks:
            print("DEBUG: No pose landmarks detected.")
            return "unknown", "unknown", frame, 0.0, None

        annotated = frame.copy()
        mp_draw.draw_landmarks(
            annotated,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        features = extract_features(results.pose_landmarks)
        X_df = create_feature_dataframe(features, self.expected_features)
        
        # DEBUG: Check if features are empty/zeros
        if X_df.iloc[0].sum() == 0:
             print("DEBUG: CRITICAL - All features are zero! Reindexing mismatch likely.")
             # print(f"DEBUG: Generated columns: {X_df.columns[:5]}")
        
        X_scaled = self.scaler.transform(X_df)

        # ROBUST PREDICTION: Bypass sklearn wrapper to avoid version attribute errors
        # 'multi:softprob' returns probabilities directly
        try:
            dmat = xgb.DMatrix(X_scaled)
            probs = self.model.get_booster().predict(dmat)[0]
            
            # DEBUG: Print Top 3
            top3_idx = np.argsort(probs)[-3:][::-1]
            top3_labels = self.label_encoder.inverse_transform(top3_idx)
            top3_probs = probs[top3_idx]
            print(f"DEBUG: Top Predictions: {list(zip(top3_labels, top3_probs))}")
            
        except Exception as e:
            print(f"DEBUG: XGB Prediction Error: {e}")
            return "unknown", "unknown", frame, 0.0, None

        idx = int(np.argmax(probs))
        confidence = float(np.max(probs) * 100)

        label = self.label_encoder.inverse_transform([idx])[0]
        print(f"DEBUG: Frame Pred: {label} ({confidence:.1f}%)")

        if "_" in label:
            exercise, form = label.rsplit("_", 1)
        else:
            exercise, form = label, "unknown"

        self.prediction_history.append((exercise, form))
        self.confidence_history.append(confidence)

        exercise, form = max(
            set(self.prediction_history),
            key=self.prediction_history.count
        )

        avg_conf = float(np.mean(self.confidence_history))

        return exercise, form, annotated, avg_conf, results.pose_landmarks

    def process_frame(self, frame, return_dual=False):
        self.frame_count += 1
        exercise, form, frame_skeleton, conf, landmarks = self.predict_exercise_and_form(frame)

        if landmarks:
            self.current_exercise = exercise
            self.current_form = form
            self.heatmap_viz.update_heatmap(landmarks.landmark, frame.shape)
            self.update_reps(landmarks, exercise)
        else:
            self.no_pose_frames += 1

        # Generate Heatmap Frame (New Copy)
        frame_heatmap = self.heatmap_viz.apply_heatmap_overlay(frame_skeleton)

        # 1. Info Panel for NORMAL (Heatmap: OFF)
        panel_normal = create_compact_info_panel(
            frame_skeleton.shape[1],
            exercise,
            form,
            conf,
            self.stage,
            COLORS,
            self.reps,
            self.hold_time,
            show_heatmap=False,
            frame_count=self.frame_count
        )
        
        # Safe Resize to ensure exact width match (OpenCV vstack strict requirement)
        if panel_normal.shape[1] != frame_skeleton.shape[1]:
             panel_normal = cv2.resize(panel_normal, (frame_skeleton.shape[1], panel_normal.shape[0]))
        
        try:
             final_normal = np.vstack([panel_normal, frame_skeleton])
        except Exception:
             # Fallback if vstack fails (e.g. channel mismatch)
             final_normal = frame_skeleton

        # 2. Info Panel for HEATMAP (Heatmap: ON)
        panel_heatmap = create_compact_info_panel(
            frame_heatmap.shape[1],
            exercise,
            form,
            conf,
            self.stage,
            COLORS,
            self.reps,
            self.hold_time,
            show_heatmap=True,
            frame_count=self.frame_count
        )
        
        if panel_heatmap.shape[1] != frame_heatmap.shape[1]:
             panel_heatmap = cv2.resize(panel_heatmap, (frame_heatmap.shape[1], panel_heatmap.shape[0]))

        try:
             final_heatmap = np.vstack([panel_heatmap, frame_heatmap])
        except Exception:
             final_heatmap = frame_heatmap

        if exercise != "unknown":
            self.exercise_counts[exercise] = self.exercise_counts.get(exercise, 0) + 1
            self.form_counts[form] += 1
            self.predictions.append((exercise, form, conf))

        if return_dual:
            return final_normal, final_heatmap

        # Legacy return if not dual
        return final_heatmap if self.heatmap_viz.show_heatmap else final_normal

    def process_video(self, input_path, output_dir="predicted_videos", enable_heatmap=True):
        self.reset_state()
        self.heatmap_viz.show_heatmap = True # Always enable internally to track heatmap state
        
        cap = cv2.VideoCapture(input_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0: fps = 30 # Fallback
        
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        ret, first = cap.read()
        if not ret:
            return {"error": "Could not read video"}

        panel = create_compact_info_panel(
            first.shape[1], "unknown", "unknown", 0.0,
            "down", COLORS, 0, 0, False, 0
        )
        h = panel.shape[0] + first.shape[0]
        w = first.shape[1]
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        os.makedirs(output_dir, exist_ok=True)
        
        uuid_str = uuid.uuid4().hex
        filename_normal = f"processed_{uuid_str}_normal.mp4"
        filename_heatmap = f"processed_{uuid_str}_heatmap.mp4"
        
        path_normal = os.path.join(output_dir, filename_normal)
        path_heatmap = os.path.join(output_dir, filename_heatmap)
        
        # Use H.264 (avc1) for better compatibility with Flutter/Web
        try:
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
            out_normal = cv2.VideoWriter(path_normal, fourcc, fps, (w, h))
            out_heatmap = cv2.VideoWriter(path_heatmap, fourcc, fps, (w, h))
        except Exception:
            # Fallback to mp4v if avc1 is not available
            print("Warning: avc1 codec not found, falling back to mp4v")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out_normal = cv2.VideoWriter(path_normal, fourcc, fps, (w, h))
            out_heatmap = cv2.VideoWriter(path_heatmap, fourcc, fps, (w, h))

        count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                count += 1
                f_normal, f_heatmap = self.process_frame(frame, return_dual=True)
                
                f_normal = cv2.resize(f_normal, (w, h))
                f_heatmap = cv2.resize(f_heatmap, (w, h))
                
                draw_progress_bar(f_normal, count, total)
                draw_progress_bar(f_heatmap, count, total)
                
                out_normal.write(f_normal)
                out_heatmap.write(f_heatmap)
                
                if count % 10 == 0:
                    print(f"Processing: {int(count/total*100)}% ({count}/{total})", end='\r')
        finally:
            cap.release()
            out_normal.release()
            out_heatmap.release()
        
        # Calculate Final Stats
        # Human Presence Validation
        valid_frames = self.frame_count - self.no_pose_frames
        print(f"DEBUG: Valid Frames with Human Pose: {valid_frames}/{self.frame_count}")

        # REJECTION LOGIC: If fewer than 5 frames had a detected person, reject the video
        if self.frame_count > 0 and valid_frames < 5:
             print("REJECTING VIDEO: No human detected.")
             # Clean up files
             try:
                 if os.path.exists(path_normal):
                     os.remove(path_normal)
                 if os.path.exists(path_heatmap):
                     os.remove(path_heatmap)
             except Exception as cleanup_err:
                 print(f"Warning: Failed to cleanup rejected video files: {cleanup_err}")

             return {"error": "No human detected in the video. Please ensure a person is visible for accurate analysis."}

        # LOGIC FIX: Use the most frequent exercise detected, NOT the last one
        final_exercise = "unknown"
        if self.exercise_counts:
            # Filter out unknown if possible
            known_exercises = {k: v for k, v in self.exercise_counts.items() if k != "unknown"}
            if known_exercises:
                final_exercise = max(known_exercises, key=known_exercises.get)
            else:
                final_exercise = max(self.exercise_counts, key=self.exercise_counts.get)
        
        final_form = "unknown"
        if self.form_counts:
             # Just take the most common form
             final_form = max(self.form_counts, key=self.form_counts.get)

        reco_data = load_recommendations(str(self.recommendations_file))
        final_recommendations = reco_data.get(
            final_exercise.lower(), {}
        ).get(final_form.lower(), [])

        avg_conf = (
            sum(p[2] for p in self.predictions) / len(self.predictions)
            if self.predictions else 0
        )
        
        return {
            "success": True,
            "exercise": final_exercise,
            "form": final_form,
            "reps": self.reps,
            "hold_time": self.hold_time,
            "confidence": avg_conf,
            "total_frames": self.frame_count,
            "no_pose_frames": self.no_pose_frames,
            "recommendations": final_recommendations,
            "processed_video_filename": filename_normal,
            "processed_video_path": path_normal,
            "video_filename_normal": filename_normal,
            "video_path_normal": path_normal,
            "video_filename_heatmap": filename_heatmap,
            "video_path_heatmap": path_heatmap
        }
# Global instance to load models once
_processor = None

def get_processor():
    global _processor
    if _processor is None:
        _processor = FitnessVideoProcessor()
    return _processor
