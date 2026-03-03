import cv2
import joblib
import os

# FIX: Set environment variable to avoid Protobuf/MediaPipe 'GetPrototype' error
# This must be set BEFORE importing mediapipe
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import mediapipe as mp
import numpy as np
import time
import uuid
import xgboost as xgb
from collections import Counter, deque
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
    from .prediction_config import PredictionConfig, QualityMetrics, get_exercise_similarity
    from .utils import (
        create_compact_info_panel,
        draw_progress_bar,
        extract_features,
        create_feature_dataframe,
        load_recommendations,
        save_detailed_report_with_recommendations
    )
    from .xai_explainer import (
        generate_form_explanation,
        generate_per_rep_data,
        aggregate_joint_importance
    )
except ImportError:
    # Fallback for direct execution/testing
    from exercise_config import EXERCISE_CONFIG, COLORS
    from heatmap import HeatmapVisualizer
    from geometry import calculate_angles_from_landmarks
    from xai_explainer import (
        generate_form_explanation,
        generate_per_rep_data,
        aggregate_joint_importance
    )
    from prediction_config import PredictionConfig, QualityMetrics, get_exercise_similarity
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
    # Robust check for solutions
    import mediapipe.solutions.pose as mp_pose_sol
    import mediapipe.solutions.drawing_utils as mp_draw_sol
    mp_pose = mp_pose_sol
    mp_draw = mp_draw_sol
except ImportError:
    try:
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
            mp_pose = mp.solutions.pose
            mp_draw = mp.solutions.drawing_utils
    except Exception:
        pass

if mp_pose is None:
    print("WARNING: MediaPipe Pose solutions not found. Fitness features might be limited.")

# ──────────────────────────────────────────────────────────
# SPEED TUNING - Adjust these to balance accuracy vs speed
# ──────────────────────────────────────────────────────────
# Process every Nth frame (2 = skip every other frame, ~2x faster)
FRAME_SKIP = 2
# Cap input video resolution (width). None = no resize
MAX_VIDEO_WIDTH = 854  # 480p landscape width
# MediaPipe model complexity: 0=fastest, 1=balanced, 2=most accurate
POSE_COMPLEXITY = 0


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
            # model_complexity=0 is ~2x faster than 1, enough for gym poses
            self.pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=POSE_COMPLEXITY,
                smooth_landmarks=True,
                min_detection_confidence=0.45,
                min_tracking_confidence=0.45
            )
        else:
            self.pose = None
            print("DEBUG: MediaPipe Pose failed to initialize.")

        self.heatmap_viz = HeatmapVisualizer()
        self.reset_state()

    def reset_state(self):
        # Use improved configuration settings
        self.prediction_history = deque(maxlen=PredictionConfig.HISTORY_WINDOW)
        self.confidence_history = deque(maxlen=PredictionConfig.HISTORY_WINDOW)
        self.reps = 0
        self.stage = "up"
        self.last_rep_time = 0
        self.MIN_REP_TIME = 0.8
        self.hold_time = 0
        self.hold_start = None
        self.current_exercise = "unknown"
        self.current_form = "unknown"
        # FIX: Confidence-weighted exercise scores (not just raw counts)
        self.exercise_weighted_scores = {}
        self.exercise_counts = {}
        # FIX: Track form PER exercise (not globally)
        self.exercise_form_counts = {}  # {exercise: {"correct": N, "wrong": M}}
        self.form_counts = {"correct": 0, "wrong": 0, "unknown": 0}  # kept for legacy
        self.predictions = []
        self.no_pose_frames = 0
        self.frame_count = 0
        # FIX: Exercise stability lock - prevents flip-flopping
        self.locked_exercise = None
        self.lock_count = 0
        self.LOCK_THRESHOLD = PredictionConfig.LOCK_THRESHOLD
        # FIX: Minimum confidence to accept a prediction
        self.MIN_CONFIDENCE = PredictionConfig.MIN_CONFIDENCE
        # FIX: Skip early frames (warm-up period)
        self.WARMUP_FRAMES = PredictionConfig.WARMUP_FRAMES
        
        # FIX: Rep counting based on video time
        self.curr_fps = 30 # Default
        self.hold_start_frame = None
        self.last_rep_frame = 0
        self.min_rep_frames = 0 # Will be calculated based on fps
        
        # FIX: Rep Classification
        self.reps_correct = 0
        self.reps_wrong = 0
        self.current_rep_forms = [] # Store forms during a rep
        self.last_rep_status = "unknown" # "correct", "wrong"

        # ======================================================
        # NEW: Advanced Analytics (Separate from ML Model)
        # ======================================================
        self.rep_durations = [] # Time per rep in seconds
        self.rep_roms = []      # Range of Motion % per rep
        self.stability_scores = [] # Variance of hip x-coord
        
        self.current_rep_start_frame = 0
        self.current_rep_min_angle = 180 # Track max depth (min angle)
        self.current_rep_max_angle = 0   # Track max extension
        
        # Stability tracking
        self.hip_x_history = deque(maxlen=30) # 1 sec window at 30fps

        # NEW: Lighting Enhancement
        self.is_dark = False
        self.lighting_enhanced = False
        self.brightness_factor = 1.0
        self.contrast_factor = 0

        # ── SHAP-Weighted Heatmap tracking ──────────────────────────
        # Stores the last real scaled feature vector so SHAP can be
        # computed the moment we lock onto an exercise.
        self._last_X_scaled = None
        # Prevent re-computing SHAP on every frame once done.
        self._shap_computed = False

    def update_reps(self, landmarks, exercise, current_form="unknown"):
        # ... (unchanged)
        if exercise not in EXERCISE_CONFIG:
            return

        cfg = EXERCISE_CONFIG[exercise]

        if cfg["type"] == "hold":
            if self.hold_start_frame is None:
                self.hold_start_frame = self.frame_count
            
            # Calculate duration based on FRAMES, not wall clock time
            # duration = (current_frame - start_frame) / fps
            frames_elapsed = self.frame_count - self.hold_start_frame
            self.hold_time = int(frames_elapsed / self.curr_fps) if self.curr_fps > 0 else 0
            return

        angles = calculate_angles_from_landmarks(landmarks, cfg)
        if "main" not in angles:
            return

        angle = angles["main"]
        
        # Collect form validity during the "active" part of the rep (stage == "down" usually means flexed/active)
        # Note: "down" in config usually means extended (start), "up" means flexed (end).
        # But logic below says: angle > down -> Extended/Standing. angle < up -> Flexed/Squatting.
        # Usually stage transitions: UP -> DOWN -> UP.
        # We want to track form while they are performing the rep.
        
        if self.stage == "down":
             self.current_rep_forms.append(current_form)

        # LOGIC: Start UP -> go DOWN -> return UP (Count)
        if angle > cfg["down"]: # Extended / Standing (End of rep)
            if self.stage == "down":
                 # Check time based on frames
                 frames_since_last = self.frame_count - self.last_rep_frame
                 min_frames = self.min_rep_frames
                 
                 if frames_since_last > min_frames:
                     self.reps += 1
                     self.last_rep_frame = self.frame_count
                     
                     # --------------------------------------------------
                     # NEW: Calculate Rep Metrics
                     # --------------------------------------------------
                     # 1. Tempo (Duration)
                     rep_duration = (self.frame_count - self.current_rep_start_frame) / self.curr_fps
                     if rep_duration > 0 and rep_duration < 10: # Filter outliers
                        self.rep_durations.append(round(rep_duration, 2))
                     
                     # 2. Range of Motion (ROM)
                     # ROM % = (Designated Start - Actual Min) / (Designated Start - Designated End)
                     # Simplified: How close did we get to the target 'up' angle?
                     # Target 'up' is the flexed state (lowest angle).
                     target_depth = cfg["up"] 
                     start_pos = cfg["down"]
                     
                     # If we went deeper than target, it's 100%+
                     # If we stayed above target, it's < 100%
                     total_range = start_pos - target_depth
                     if total_range > 0:
                        achieved_range = start_pos - self.current_rep_min_angle
                        rom_pct = (achieved_range / total_range) * 100
                        rom_pct = max(0, min(100, rom_pct)) # Cap at 0-100%
                        self.rep_roms.append(round(rom_pct, 1))

                     # CLASSIFY REP (Existing Logic)
                     if self.current_rep_forms:
                         valid_forms = [f for f in self.current_rep_forms if f != "unknown"]
                         if not valid_forms: 
                             self.last_rep_status = "unknown"
                         else:
                             correct_cnt = valid_forms.count("correct")
                             wrong_cnt = valid_forms.count("wrong")
                             total_valid = correct_cnt + wrong_cnt
                             
                             # If even 5% of the active phase is marked as wrong by the model, it's a bad rep.
                             if total_valid > 0 and (wrong_cnt / total_valid) >= 0.05:
                                 self.reps_wrong += 1
                                 self.last_rep_status = "wrong"
                             elif total_valid > 0:
                                 self.reps_correct += 1
                                 self.last_rep_status = "correct"
                             else:
                                 self.last_rep_status = "unknown"
                     else:
                         self.last_rep_status = "unknown"
                         
                     # Reset for next rep
                     self.current_rep_forms = []
                     self.current_rep_min_angle = 180 # Reset depth tracker

            self.stage = "up"
            self.current_rep_max_angle = max(self.current_rep_max_angle, angle)

        if angle < cfg["up"]: # Flexed / Squatting (Start of rep / Active phase)
            if self.stage == "up":
                # Just started the rep
                self.current_rep_start_frame = self.frame_count
                self.current_rep_min_angle = angle
            
            self.stage = "down"
            self.current_rep_min_angle = min(self.current_rep_min_angle, angle)
            
        # Track angles continuously for this rep
        if self.stage == "down":
             self.current_rep_min_angle = min(self.current_rep_min_angle, angle)

    def is_workout_visibility(self, landmarks):
        """Checks if enough critical body parts are visible for a workout"""
        if not landmarks: return False
        
        # Threshold for visibility consider 'visible'
        # ↑ Raised from 0.5 to 0.65 to be more strict about body presence
        threshold = 0.65
        
        # Check groups: Shoulders(11,12), Hips(23,24), Knees(25,26)
        s_vis = landmarks.landmark[11].visibility > threshold or landmarks.landmark[12].visibility > threshold
        h_vis = landmarks.landmark[23].visibility > threshold or landmarks.landmark[24].visibility > threshold
        k_vis = landmarks.landmark[25].visibility > threshold or landmarks.landmark[26].visibility > threshold
        
        # Must have at least 2 sections visible (e.g. Shoulders+Hips or Hips+Knees)
        visible_groups = (1 if s_vis else 0) + (1 if h_vis else 0) + (1 if k_vis else 0)
        return visible_groups >= 2

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
        
        # ── NEW: Workout Visibility Check ──
        # If too few body joints are visible (e.g. just a face), reject the frame immediately
        if not self.is_workout_visibility(results.pose_landmarks):
            print("DEBUG: Non-workout view (face/limited body). Marking as unknown.")
            return "unknown", "unknown", annotated, 0.0, results.pose_landmarks

        # --------------------------------------------------
        # NEW: Stability Tracking (Hip Center Variance)
        # --------------------------------------------------
        # Hip center x is roughly average of left (23) and right (24) hip x
        try:
             # Landmarks 23 and 24 are hips
             # Index in features (flat list): 23*4, 24*4
             # But features list is [x,y,z,v, x,y,z,v...]
             # extract_features returns 33 landmarks * 4 values
             
             # Get raw landmarks for better precision
             left_hip = results.pose_landmarks.landmark[23]
             right_hip = results.pose_landmarks.landmark[24]
             hip_center_x = (left_hip.x + right_hip.x) / 2.0
             
             self.hip_x_history.append(hip_center_x)
             
             if len(self.hip_x_history) >= 10:
                 variance = np.var(list(self.hip_x_history))
                 # Stability Score: 100 - (variance * scaling_factor)
                 # Variance usually 0.0001 (super stable) to 0.01 (shaky)
                 score = max(0, 100 - (variance * 10000))
                 self.stability_scores.append(score)
        except Exception:
             pass

        X_df = create_feature_dataframe(features, self.expected_features)
        
        # DEBUG: Check if features are empty/zeros
        if X_df.iloc[0].sum() == 0:
             print("DEBUG: CRITICAL - All features are zero! Reindexing mismatch likely.")
        
        X_scaled = self.scaler.transform(X_df)

        # ── Cache real features for SHAP computation on lock ─────────
        self._last_X_scaled = X_scaled

        # ROBUST PREDICTION: Bypass sklearn wrapper to avoid version attribute errors
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

        # ============================================================
        # FIX 1: Skip warm-up frames (early frames are often noisy)
        # ============================================================
        if self.frame_count <= self.WARMUP_FRAMES:
            # During warmup return 'initializing' so the video overlay
            # doesn't flash wrong exercise names at the very start
            return "initializing", "unknown", annotated, confidence, results.pose_landmarks

        # ============================================================
        # FIX 2: Only accept predictions above confidence threshold
        # ============================================================
        if confidence < self.MIN_CONFIDENCE:
            print(f"DEBUG: Low confidence {confidence:.1f}% < {self.MIN_CONFIDENCE}% - SKIPPING")
            # Still return landmarks for heatmap but don't pollute history
            avg_conf = float(np.mean(self.confidence_history)) if self.confidence_history else 0
            prev_ex = self.current_exercise if self.current_exercise != "unknown" else exercise
            prev_form = self.current_form if self.current_form != "unknown" else form
            return prev_ex, prev_form, annotated, avg_conf, results.pose_landmarks

        # ============================================================
        # FIX 5: Distinguish Pull Up vs Lat Pulldown (Body Movement)
        # ============================================================
        if exercise in ["pull_up", "lat_pulldown"]:
            try:
                landmarks = results.pose_landmarks.landmark
                # Monitor vertical movement of shoulders vs wrists
                left_shoulder_y = landmarks[11].y
                right_shoulder_y = landmarks[12].y
                left_wrist_y = landmarks[15].y
                right_wrist_y = landmarks[16].y
                
                avg_shoulder_y = (left_shoulder_y + right_shoulder_y) / 2
                avg_wrist_y = (left_wrist_y + right_wrist_y) / 2
                
                # Initialize history buffers if needed
                if not hasattr(self, "shoulder_y_history"):
                    self.shoulder_y_history = deque(maxlen=30)
                    self.wrist_y_history = deque(maxlen=30)
                
                self.shoulder_y_history.append(avg_shoulder_y)
                self.wrist_y_history.append(avg_wrist_y)
                
                # Only check after accumulating ~0.5s of history
                if len(self.shoulder_y_history) > 15:
                    shoulder_var = np.var(self.shoulder_y_history)
                    wrist_var = np.var(self.wrist_y_history)
                    
                    # LOGIC:
                    # Pull Up: Hands on bar (fixed), Body moves (shoulders move) -> Shoulder Var > Wrist Var
                    # Lat Pulldown: Body seated (fixed), Hands pull bar (wrists move) -> Wrist Var > Shoulder Var
                    
                    if shoulder_var > wrist_var * 2.0:
                        if exercise == "lat_pulldown":
                            print(f"DEBUG: Correction! Shoulders moving ({shoulder_var:.5f}) > Wrists ({wrist_var:.5f}) -> Forced PULL_UP")
                            exercise = "pull_up"
                            confidence = 98.0  # Boost confidence to break lock
                            
                    elif wrist_var > shoulder_var * 2.0:
                        if exercise == "pull_up":
                            print(f"DEBUG: Correction! Wrists moving ({wrist_var:.5f}) > Shoulders ({shoulder_var:.5f}) -> Forced LAT_PULLDOWN")
                            exercise = "lat_pulldown"
                            confidence = 98.0  # Boost confidence to break lock
                            
            except Exception as e:
                print(f"DEBUG: Heuristic check failed: {e}")

        # ============================================================
        # FIX 3: Exercise stability lock - prevent flip-flopping
        # ============================================================
        if self.locked_exercise is not None:
            # Exercise is locked - only accept same exercise predictions
            if exercise != self.locked_exercise:
                # Check for similarity
                similarity = get_exercise_similarity(exercise, self.locked_exercise)
                
                # Determine threshold based on similarity
                # If highly similar (e.g. Bicep Curl vs Deadlift setup), be more lenient to switch
                break_threshold = PredictionConfig.HIGH_CONFIDENCE
                if similarity >= 0.5:
                     break_threshold = PredictionConfig.CONFIDENCE_MEDIUM
                     print(f"DEBUG: Similar exercises ({exercise} vs {self.locked_exercise}, sim={similarity:.2f}). Lowering break threshold to {break_threshold}")

                # Different exercise detected, but we're locked
                # Allow override ONLY if confidence is high enough
                if confidence > break_threshold:
                    self.lock_count -= PredictionConfig.LOCK_EROSION_RATE  # Erode lock
                    
                    # Bonus erosion if really similar (makes switching even faster)
                    if similarity >= 0.5:
                        self.lock_count -= 2

                    if self.lock_count <= 0:
                        print(f"DEBUG: LOCK BROKEN - Switching from {self.locked_exercise} to {exercise}")
                        self.locked_exercise = exercise
                        self.lock_count = 5
                else:
                    # Keep locked exercise, ignore this frame's exercise
                    exercise = self.locked_exercise
            else:
                self.lock_count = min(self.lock_count + 1, self.LOCK_THRESHOLD * 2)
        else:
            # No lock yet - check if we should lock
            self.prediction_history.append((exercise, form))
            self.confidence_history.append(confidence)
            
            # Count consecutive same-exercise predictions
            recent_exercises = [p[0] for p in self.prediction_history]
            if len(recent_exercises) >= self.LOCK_THRESHOLD:
                counts = Counter(recent_exercises[-self.LOCK_THRESHOLD:])
                top_exercise, top_count = counts.most_common(1)[0]
                if top_count >= self.LOCK_THRESHOLD * PredictionConfig.LOCK_AGREEMENT:
                    self.locked_exercise = top_exercise
                    self.lock_count = top_count
                    print(f"DEBUG: EXERCISE LOCKED -> {self.locked_exercise} ({top_count}/{self.LOCK_THRESHOLD})")

                    # ── SHAP-Weighted Heatmap: compute on first lock ─────
                    if not self._shap_computed and self._last_X_scaled is not None:
                        try:
                            import shap as _shap
                            _booster = self.model.get_booster()
                            _explainer = _shap.TreeExplainer(_booster)
                            _X_dm = xgb.DMatrix(
                                self._last_X_scaled,
                                feature_names=list(self.expected_features)
                            )
                            _shap_vals = _explainer.shap_values(_X_dm)
                            if isinstance(_shap_vals, list):
                                # Multi-class: sum absolute SHAP across all classes
                                _combined = np.sum(
                                    [np.abs(sv) for sv in _shap_vals], axis=0
                                )
                                _ji = aggregate_joint_importance(
                                    _combined[0], self.expected_features
                                )
                            else:
                                _ji = aggregate_joint_importance(
                                    _shap_vals[0], self.expected_features
                                )
                            if _ji:
                                self.heatmap_viz.update_shap_weights(_ji)
                                print(f"[SHAP Heatmap] Weights applied for "
                                      f"'{self.locked_exercise}': "
                                      f"{list(_ji.items())[:5]}")
                            self._shap_computed = True
                        except ImportError:
                            print("[SHAP Heatmap] 'shap' not installed — "
                                  "staying in motion mode.")
                            self._shap_computed = True  # don't retry
                        except Exception as _shap_err:
                            print(f"[SHAP Heatmap] Computation error: {_shap_err}")
                            self._shap_computed = True  # don't retry

        # Add to history (after potential lock adjustment)
        self.prediction_history.append((exercise, form))
        self.confidence_history.append(confidence)

        # ============================================================
        # FIX 4: Final smoothed prediction for DISPLAY
        # Priority: locked exercise > majority vote in recent history
        # ============================================================
        if self.locked_exercise is not None:
            # Lock is established — always display the locked exercise
            display_exercise = self.locked_exercise
            # Still compute smoothed form from history
            recent_forms = [p[1] for p in self.prediction_history
                            if p[0] == self.locked_exercise]
            display_form = Counter(recent_forms).most_common(1)[0][0] \
                           if recent_forms else form
        else:
            # No lock yet — majority vote in recent window
            display_exercise, display_form = max(
                set(self.prediction_history),
                key=self.prediction_history.count
            )

        avg_conf = float(np.mean(self.confidence_history))

        return display_exercise, display_form, annotated, avg_conf, results.pose_landmarks

    def process_frame(self, frame, return_dual=False):
        self.frame_count += 1
        
        # ── NEW: Lighting Enhancement ──
        if self.is_dark:
            # Apply enhancement (Brightness/Contrast)
            # F(x) = alpha*x + beta
            frame = cv2.convertScaleAbs(frame, alpha=self.brightness_factor, beta=self.contrast_factor)
            self.lighting_enhanced = True

        exercise, form, frame_skeleton, conf, landmarks = self.predict_exercise_and_form(frame)

        if landmarks:
            self.current_exercise = exercise
            self.current_form = form
            self.heatmap_viz.update_heatmap(landmarks.landmark, frame.shape)
            self.update_reps(landmarks, exercise, current_form=form)
        else:
            self.no_pose_frames += 1

        # Generate Heatmap Frame (New Copy) - must be done AFTER skeleton frame is ready
        frame_heatmap = self.heatmap_viz.apply_heatmap_overlay(frame_skeleton.copy())

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
            frame_count=self.frame_count,
            last_rep_status=self.last_rep_status,
            reps_correct=self.reps_correct,
            reps_wrong=self.reps_wrong
        )
        
        # Safe Resize to ensure exact width match (OpenCV vstack strict requirement)
        if panel_normal.shape[1] != frame_skeleton.shape[1]:
             panel_normal = cv2.resize(panel_normal, (frame_skeleton.shape[1], panel_normal.shape[0]))
        
        # Ensure both have same number of channels
        if panel_normal.shape[2] != frame_skeleton.shape[2]:
            if frame_skeleton.shape[2] == 3 and panel_normal.shape[2] == 1:
                panel_normal = cv2.cvtColor(panel_normal, cv2.COLOR_GRAY2BGR)
            elif frame_skeleton.shape[2] == 1 and panel_normal.shape[2] == 3:
                frame_skeleton = cv2.cvtColor(frame_skeleton, cv2.COLOR_GRAY2BGR)
        
        try:
             final_normal = np.vstack([panel_normal, frame_skeleton])
        except Exception as e:
             # Fallback if vstack fails (e.g. channel mismatch)
             print(f"Warning: vstack failed for normal frame: {e}")
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
            frame_count=self.frame_count,
            last_rep_status=self.last_rep_status,
            reps_correct=self.reps_correct,
            reps_wrong=self.reps_wrong
        )
        
        if panel_heatmap.shape[1] != frame_heatmap.shape[1]:
             panel_heatmap = cv2.resize(panel_heatmap, (frame_heatmap.shape[1], panel_heatmap.shape[0]))

        # Ensure both have same number of channels
        if panel_heatmap.shape[2] != frame_heatmap.shape[2]:
            if frame_heatmap.shape[2] == 3 and panel_heatmap.shape[2] == 1:
                panel_heatmap = cv2.cvtColor(panel_heatmap, cv2.COLOR_GRAY2BGR)
            elif frame_heatmap.shape[2] == 1 and panel_heatmap.shape[2] == 3:
                frame_heatmap = cv2.cvtColor(frame_heatmap, cv2.COLOR_GRAY2BGR)

        try:
             final_heatmap = np.vstack([panel_heatmap, frame_heatmap])
        except Exception as e:
             print(f"Warning: vstack failed for heatmap frame: {e}")
             final_heatmap = frame_heatmap

        # Only accumulate for real (non-warmup, non-unknown) predictions
        if exercise not in ("unknown", "initializing"):
            self.exercise_counts[exercise] = self.exercise_counts.get(exercise, 0) + 1
            # Confidence-weighted scoring
            weight = max(conf / 100.0, 0.1)
            self.exercise_weighted_scores[exercise] = self.exercise_weighted_scores.get(exercise, 0) + weight
            # Track form PER exercise
            if exercise not in self.exercise_form_counts:
                self.exercise_form_counts[exercise] = {"correct": 0, "wrong": 0, "unknown": 0}
            if form in self.exercise_form_counts[exercise]:
                self.exercise_form_counts[exercise][form] += 1
            self.form_counts[form] += 1
            self.predictions.append((exercise, form, conf))

        if return_dual:
            return final_normal, final_heatmap

        # Legacy return if not dual
        return final_heatmap if self.heatmap_viz.show_heatmap else final_normal

    def process_video(self, input_path, output_dir="predicted_videos", enable_heatmap=True):
        self.reset_state()
        self.heatmap_viz.reset() # Reset heatmap state to avoid dimension mismatch/ghosting
        self.heatmap_viz.show_heatmap = True # Always enable internally to track heatmap state
        
        cap = cv2.VideoCapture(input_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0: fps = 30 # Fallback
        
        # ────────────────────────────────────────────────────────
        # SPEED FIX: Effective fps after frame skipping
        # Rep counting already uses frame indices so we adjust
        # ────────────────────────────────────────────────────────
        effective_fps = fps // FRAME_SKIP
        if effective_fps == 0: effective_fps = fps
        self.curr_fps = effective_fps
        self.min_rep_frames = int(self.MIN_REP_TIME * effective_fps)
        
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_effective = max(1, total // FRAME_SKIP)
        
        ret, first = cap.read()
        if not ret:
            return {"error": "Could not read video"}

        # ── NEW: Dark Light Detection ──
        try:
            gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)
            if avg_brightness < 70: # Standard threshold for low light
                self.is_dark = True
                # Increase brightness by 40% and add baseline contrast
                self.brightness_factor = 1.4
                self.contrast_factor = 25
                print(f"DEBUG: Low light detected (avg={avg_brightness:.1f}). Enabling enhancement.")
        except Exception as e:
            print(f"Lighting detection error: {e}")

        # ────────────────────────────────────────────────────────
        # SPEED FIX: Cap resolution to MAX_VIDEO_WIDTH
        # e.g. 1920x1080 → 854x480 (4x fewer pixels to process)
        # ────────────────────────────────────────────────────────
        orig_h, orig_w = first.shape[:2]
        if MAX_VIDEO_WIDTH and orig_w > MAX_VIDEO_WIDTH:
            scale = MAX_VIDEO_WIDTH / orig_w
            proc_w = MAX_VIDEO_WIDTH
            proc_h = int(orig_h * scale)
        else:
            proc_w, proc_h = orig_w, orig_h
        
        print(f"DEBUG: Video {orig_w}x{orig_h} → processing at {proc_w}x{proc_h}, frame_skip={FRAME_SKIP}")

        panel = create_compact_info_panel(
            proc_w, "unknown", "unknown", 0.0,
            "down", COLORS, 0, 0, False, 0
        )
        h = panel.shape[0] + proc_h
        w = proc_w
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        os.makedirs(output_dir, exist_ok=True)
        
        uuid_str = uuid.uuid4().hex
        filename_normal = f"processed_{uuid_str}_normal.mp4"
        filename_heatmap = f"processed_{uuid_str}_heatmap.mp4"
        
        path_normal = os.path.join(output_dir, filename_normal)
        path_heatmap = os.path.join(output_dir, filename_heatmap)
        
        # ────────────────────────────────────────────────────────
        # CODEC SELECTION: Prefer mp4v on Windows (very stable)
        # ────────────────────────────────────────────────────────
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        
        # SLOW DOWN PLAYBACK: Use half FPS for output
        out_fps = max(fps / 2.0, 10.0)
        print(f"DEBUG: Input FPS={fps}, Output Video FPS={out_fps} (Slow Motion)")

        out_normal = cv2.VideoWriter(path_normal, fourcc, out_fps, (w, h))
        
        # CRITICAL FIX: Robust codec fallback for Windows
        if not out_normal.isOpened():
            print(f"Warning: mp4v failed. Trying alternative codecs...")
            for alt_codec in ["XVID", "X264", "MJPG"]:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*alt_codec)
                    out_normal = cv2.VideoWriter(path_normal, fourcc, out_fps, (w, h))
                    if out_normal.isOpened():
                         print(f"✅ Successfully initialized video writer with {alt_codec}")
                         break
                except: continue
            
            if not out_normal.isOpened():
                 return {"error": "Server Video Encoding Error: Could not initialize video writer. Check server FFmpeg installation."}

        out_heatmap = None
        if enable_heatmap:
            out_heatmap = cv2.VideoWriter(path_heatmap, fourcc, out_fps, (w, h))
            if not out_heatmap.isOpened():
                print(f"Warning: Failed to open heatmap writer. Disabling heatmap.")
                enable_heatmap = False
                out_heatmap = None

        raw_frame_count = 0
        count = 0  # effective (processed) frame counter
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                raw_frame_count += 1

                # ── SPEED FIX: Skip frames ──
                if raw_frame_count % FRAME_SKIP != 0:
                    continue

                count += 1

                # ── SPEED FIX: Resize frame before processing ──
                if MAX_VIDEO_WIDTH and frame.shape[1] > MAX_VIDEO_WIDTH:
                    frame = cv2.resize(frame, (proc_w, proc_h))

                f_normal, f_heatmap = self.process_frame(frame, return_dual=True)
                
                # Double check sizes match writer
                if (f_normal.shape[1] != w) or (f_normal.shape[0] != h):
                     f_normal = cv2.resize(f_normal, (w, h))
                
                draw_progress_bar(f_normal, count, total_effective)
                out_normal.write(f_normal)
                
                if enable_heatmap and out_heatmap is not None:
                     f_heatmap = cv2.resize(f_heatmap, (w, h))
                     draw_progress_bar(f_heatmap, count, total_effective)
                     out_heatmap.write(f_heatmap)
                
                if count % 10 == 0:
                    pct = int(count / total_effective * 100) if total_effective > 0 else 0
                    print(f"Processing: {pct}% ({count}/{total_effective} effective frames)", end='\r')
        finally:
            cap.release()
            out_normal.release()
            if out_heatmap is not None:
                out_heatmap.release()
        
        # Calculate Final Stats
        # Human Presence Validation
        valid_frames = self.frame_count - self.no_pose_frames
        print(f"DEBUG: Valid Frames with Human Pose: {valid_frames}/{self.frame_count}")

        # REJECTION LOGIC: If fewer than 20 frames had a REAL exercise, reject it (as per user request)
        workout_frames = sum(v for k, v in self.exercise_counts.items() if k not in ("unknown", "initializing"))
        if workout_frames < 20:
             print(f"REJECTING VIDEO: Too few workout frames ({workout_frames}/20 needed).")
             # Clean up
             try:
                 if os.path.exists(path_normal): os.remove(path_normal)
                 if os.path.exists(path_heatmap): os.remove(path_heatmap)
             except: pass
             return {"error": "This does not appear to be a correct workout video. Please ensure your full body is visible (at least shoulders to hips) and perform the exercise clearly for at least 5 seconds."}

        # Human Presence Validation
        if self.frame_count > 0 and valid_frames < PredictionConfig.MIN_VALID_FRAMES:
             print(f"REJECTING VIDEO: Insufficient pose detection ({valid_frames}/{self.frame_count} frames).")
             # Clean up files
             try:
                 if os.path.exists(path_normal):
                     os.remove(path_normal)
                 if os.path.exists(path_heatmap):
                     os.remove(path_heatmap)
             except Exception as cleanup_err:
                 print(f"Warning: Failed to cleanup rejected video files: {cleanup_err}")

             return {"error": "No human detected in the video. Please ensure a person is fully visible for accurate analysis."}

        # ============================================================
        # FINAL RESULT: Prioritise lock → raw frame count → weighted score
        # ============================================================
        # NOTE: We use RAW FRAME COUNTS (exercise_counts) as the primary
        # fallback because these directly reflect what the video overlay
        # showed frame-by-frame. Using weighted scores could pick an
        # exercise that never dominated the display.
        # ============================================================
        final_exercise = "unknown"

        # Filter out "initializing" and "unknown" from all dicts
        valid_counts = {k: v for k, v in self.exercise_counts.items()
                        if k not in ("unknown", "initializing") and v > 0}

        # Priority 1: locked exercise (most stable — use if in valid counts)
        if self.locked_exercise and self.locked_exercise in valid_counts:
            final_exercise = self.locked_exercise
            print(f"✅ Final exercise from LOCK: {final_exercise} "
                  f"(frames={valid_counts[self.locked_exercise]})")

        # Priority 2: highest raw frame count
        elif valid_counts:
            final_exercise = max(valid_counts, key=valid_counts.get)
            total = sum(valid_counts.values())
            pct   = valid_counts[final_exercise] / total * 100
            print(f"✅ Final exercise from FRAME COUNT: {final_exercise} "
                  f"({valid_counts[final_exercise]}/{total} frames = {pct:.0f}%)")
            print(f"   All exercise counts: {valid_counts}")

        # Priority 3: fallback to weighted scores if counts empty
        elif self.exercise_weighted_scores:
            known_scores = {k: v for k, v in self.exercise_weighted_scores.items()
                            if k not in ("unknown", "initializing")}
            if known_scores:
                final_exercise = max(known_scores, key=known_scores.get)
                print(f"✅ Final exercise from WEIGHTED SCORE (fallback): {final_exercise}")

        # ── NEW: Strict Exercise Validation ──
        if final_exercise in ("unknown", "initializing"):
             print(f"REJECTING VIDEO: Could not identify a valid exercise.")
             try:
                 if os.path.exists(path_normal): os.remove(path_normal)
                 if os.path.exists(path_heatmap): os.remove(path_heatmap)
             except: pass
             return {"error": "The AI could not confidently identify your exercise. Please ensure you are performing one of the supported exercises clearly and fully visible."}

        
        # ============================================================
        # FIX: Get form for the DETECTED exercise only (not globally)
        # 🚨 STRONGER WRONG VIDEO IDENTIFICATION 🚨 
        final_form = "correct" # default
        
        # Calculate Averages for Advanced Metrics
        avg_rom = np.mean(self.rep_roms) if self.rep_roms else 0.0
        avg_tempo = np.mean(self.rep_durations) if self.rep_durations else 0.0
        avg_stability = np.mean(self.stability_scores) if self.stability_scores else 0.0

        # CRITICAL QUALITY CHECKS:
        # 1. ROM CHECK: If they are doing 'half-reps' (< 45% ROM), it's WRONG.
        # 2. STABILITY CHECK: If they are shaking too much (< 50% stability), it's WRONG.
        # 3. REP BREAKDOWN: If even ONE rep was marked wrong, or > 2% of frames were wrong.

        is_poor_quality = False
        quality_reason = ""

        if self.reps > 0:
            if avg_rom < 45.0:
                is_poor_quality = True
                quality_reason = f"Low Range of Motion ({avg_rom:.1f}%)"
            elif avg_stability < 50.0:
                is_poor_quality = True
                quality_reason = f"Poor Stability ({avg_stability:.1f}%)"

        if is_poor_quality:
            final_form = "wrong"
            print(f"--> QUALITY REJECTION: Classified as WRONG due to {quality_reason}.")
        elif self.reps_wrong > 0:
            final_form = "wrong"
            print(f"--> REP THRESHOLD REACHED: Classifying video as WRONG because {self.reps_wrong} bad reps were detected.")
        elif final_exercise in self.exercise_form_counts:
            ex_forms = self.exercise_form_counts[final_exercise]
            
            correct_count = ex_forms.get("correct", 0)
            wrong_count = ex_forms.get("wrong", 0)
            total_known = correct_count + wrong_count
            
            if total_known > 0:
                wrong_ratio = wrong_count / total_known
                print(f"DEBUG: Form counts for '{final_exercise}': Correct={correct_count}, Wrong={wrong_count}. Wrong Ratio: {wrong_ratio:.2f}")
                
                # If even 2% of the frames are marked wrong, flag it (even more strict)
                if wrong_ratio >= 0.02:
                    final_form = "wrong"
                    print("--> EXCEPTION THRESHOLD REACHED: Classifying video as WRONG due to significant bad form frames.")
                else:
                    final_form = "correct"
                    
        elif self.form_counts:
            known_forms = {k: v for k, v in self.form_counts.items() if k != "unknown" and v > 0}
            if known_forms:
                correct_g = known_forms.get("correct", 0)
                wrong_g = known_forms.get("wrong", 0)
                if (correct_g + wrong_g) > 0 and (wrong_g / (correct_g + wrong_g)) >= 0.06: # Also lowered from 0.075
                    final_form = "wrong"
                else:
                    final_form = "correct"

        reco_data = load_recommendations(str(self.recommendations_file))
        final_recommendations = reco_data.get(
            final_exercise.lower(), {}
        ).get(final_form.lower(), [])

        # Calculate confidence only from predictions of the FINAL exercise
        exercise_preds = [p for p in self.predictions if p[0] == final_exercise]
        avg_conf = (
            sum(p[2] for p in exercise_preds) / len(exercise_preds)
            if exercise_preds else
            (sum(p[2] for p in self.predictions) / len(self.predictions) if self.predictions else 0)
        )
        
        # Determine confidence level for frontend
        if avg_conf >= PredictionConfig.CONFIDENCE_HIGH:
            confidence_level = "high"
        elif avg_conf >= PredictionConfig.CONFIDENCE_MEDIUM:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Assess video quality and provide recommendations
        quality_assessment = QualityMetrics.assess_video_quality(
            self.predictions, self.frame_count, valid_frames
        )
        
        # Calculate Averages for Advanced Metrics
        avg_rom = np.mean(self.rep_roms) if self.rep_roms else 0.0
        avg_tempo = np.mean(self.rep_durations) if self.rep_durations else 0.0
        avg_stability = np.mean(self.stability_scores) if self.stability_scores else 0.0

        # ──────────────────────────────────────────────────────────
        # XAI: SHAP Feature Importance + Natural Language Explanations
        # ──────────────────────────────────────────────────────────
        joint_importance = {}
        try:
            import shap
            # Use Tree explainer for XGBoost (fast)
            booster = self.model.get_booster()
            explainer = shap.TreeExplainer(booster)
            
            # Get a representative sample (last processed frame features)
            if self.predictions:
                # Use the last valid prediction's features
                last_features = extract_features(None)  # placeholder
                # Better: use stored X_scaled from final exercise frames
                # Build a representative input from stored predictions
                sample_features = np.zeros(len(self.expected_features))
                X_sample = xgb.DMatrix(sample_features.reshape(1, -1),
                                        feature_names=list(self.expected_features))
                try:
                    shap_values = explainer.shap_values(X_sample)
                    if isinstance(shap_values, list):
                        # Multi-class: sum absolute SHAP across all classes
                        combined = np.sum([np.abs(sv) for sv in shap_values], axis=0)
                        joint_importance = aggregate_joint_importance(
                            combined[0], self.expected_features
                        )
                    else:
                        joint_importance = aggregate_joint_importance(
                            shap_values[0], self.expected_features
                        )
                except Exception as shap_err:
                    print(f"SHAP computation error: {shap_err}")
        except ImportError:
            print("SHAP not installed – skipping feature importance.")
        except Exception as xai_err:
            print(f"XAI feature importance error: {xai_err}")

        # Generate natural language XAI explanation
        xai_explanation = {}
        try:
            xai_explanation = generate_form_explanation(
                exercise=final_exercise,
                form=final_form,
                avg_rom=avg_rom,
                avg_stability=avg_stability,
                avg_tempo=avg_tempo,
                reps_correct=self.reps_correct,
                reps_wrong=self.reps_wrong,
                reps_total=self.reps,
                joint_importance=joint_importance,
                confidence=avg_conf
            )
        except Exception as explain_err:
            print(f"XAI explanation error: {explain_err}")

        # Generate per-rep quality timeline
        per_rep_timeline = []
        try:
            per_rep_timeline = generate_per_rep_data(
                rep_roms=self.rep_roms,
                rep_durations=self.rep_durations,
                reps_correct=self.reps_correct,
                reps_wrong=self.reps_wrong,
                reps_total=self.reps
            )
        except Exception as rep_err:
            print(f"Per-rep timeline error: {rep_err}")

        return {
            "success": True,
            "exercise": final_exercise,
            "form": final_form,
            "reps": self.reps,
            "reps_correct": self.reps_correct,
            "reps_wrong": self.reps_wrong,
            "hold_time": self.hold_time,
            "confidence": avg_conf,
            "confidence_level": confidence_level,
            "total_frames": self.frame_count,
            "no_pose_frames": self.no_pose_frames,
            "recommendations": final_recommendations,
            "exercise_scores": self.exercise_weighted_scores,
            "processed_video_filename": filename_normal,
            "processed_video_path": path_normal,
            "video_filename_normal": filename_normal,
            "video_path_normal": path_normal,
            # Conditionally add heatmap info
            **({
                "video_filename_heatmap": filename_heatmap,
                "video_path_heatmap": path_heatmap,
            } if enable_heatmap else {}),
            "quality": quality_assessment["quality"],
            "quality_issues": quality_assessment["issues"],
            "quality_recommendations": quality_assessment["recommendations"],
            
            # NEW: Advanced Analytics Data
            "advanced_metrics": {
                "avg_rom": round(avg_rom, 1),
                "avg_tempo": round(avg_tempo, 2),
                "avg_stability": round(avg_stability, 1),
                "rep_durations": self.rep_durations,
                "rep_roms": self.rep_roms
            },
            "lighting_enhanced": self.lighting_enhanced,
            "lighting_message": "Low light detected. System has automatically enhanced the video brightness for better analysis." if self.lighting_enhanced else None,
            
            # NEW: XAI (Explainable AI) Data
            "xai_explanation": xai_explanation,
            "joint_importance": joint_importance,
            "per_rep_timeline": per_rep_timeline,
        }
# Global instance to load models once
_processor = None

def get_processor():
    global _processor
    if _processor is None:
        _processor = FitnessVideoProcessor()
    return _processor
