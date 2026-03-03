"""
mental_health.py  –  Well360 Mental-Health Router
===================================================
Upgraded pipeline (v2):

  VIDEO PREDICTION
  ────────────────
  • FER library (MTCNN face detector + deep emotion model)
    replaces the fragile Haar-Cascade + shallow 3-layer CNN.
  • CLAHE + bilateral-filter preprocessing normalises real-world lighting.
  • Temporal-weighted frame sampling (middle frames weighted ×1.5).
  • Full softmax probability accumulation instead of argmax voting.
  • Blur-rejection filter discards motion-blurred frames.
  • Calibrated confidence (dominant_prob / sum_all_probs).

  RECOMMENDATIONS
  ───────────────
  • All endpoints feed through get_personalized_recommendations().
  • Same emotion → different phrases per user (rotation + context flags).
  • Context flags: chronic_stress, improving, first_time, time_of_day.
  • Responses include rec_context dict for the Flutter UI badge.
"""

import os
import sys
import json
import base64
import uuid
import traceback
import datetime as dt_module
from io import BytesIO
from collections import Counter
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from core.models import User, MentalHealthAnalysis
from core.deps import get_current_user
from core.database import get_db

router = APIRouter(prefix="/mental-health", tags=["Mental Health"])

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONFIG
# ─────────────────────────────────────────────────────────────────────────────
MENTAL_H_DIR          = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Mental-H", "Emotional")
AUDIO_MODEL_DIR       = os.path.join(MENTAL_H_DIR, "AudioModel")
VIDEO_REC_FILE        = os.path.join(MENTAL_H_DIR, "recommendations.json")
AUDIO_REC_FILE        = os.path.join(AUDIO_MODEL_DIR, "recommendationA.json")

EMOTION_CLASSES = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]
STRESS_EMOTIONS = {"sad", "angry", "fear", "disgust"}

# ─────────────────────────────────────────────────────────────────────────────
# LAZY-LOADED MODELS
# ─────────────────────────────────────────────────────────────────────────────
_video_model = None   # FER detector
_audio_model = None   # Random Forest


def _get_video_model():
    """
    Lazy-load the FER face emotion detector (MTCNN + deep model).

    Falls back to a lightweight OpenCV+CNN combo if FER is not installed,
    so the server never crashes on cold-start even without the package.
    """
    global _video_model
    if _video_model is not None:
        return _video_model

    # ── PRIMARY: FER with MTCNN ──────────────────────────────────────────────
    try:
        # fer v25+ moved FER class to fer.fer submodule
        try:
            from fer.fer import FER
        except ImportError:
            from fer import FER  # older versions
        detector = FER(mtcnn=True)
        _video_model = {"detector": detector, "backend": "fer"}
        print("[Mental-H] FER model (MTCNN) loaded successfully ✅")
        return _video_model
    except Exception as fer_err:
        print(f"[Mental-H] FER not available ({fer_err}). Falling back to CNN …")

    # ── FALLBACK: original EmotionCNN ────────────────────────────────────────
    try:
        import torch
        from torchvision import transforms

        if MENTAL_H_DIR not in sys.path:
            sys.path.insert(0, MENTAL_H_DIR)

        from other import EmotionCNN
        from config import DEVICE

        model_path = os.path.join(MENTAL_H_DIR, "emotion_model.pth")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"CNN model not found: {model_path}")

        cnn = EmotionCNN()
        cnn.load_state_dict(torch.load(model_path, map_location=DEVICE))
        cnn.to(DEVICE)
        cnn.eval()

        transform = transforms.Compose([
            transforms.Grayscale(),
            transforms.Resize((48, 48)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])

        _video_model = {"model": cnn, "transform": transform, "device": DEVICE, "backend": "cnn"}
        print("[Mental-H] Fallback CNN model loaded ✅")
        return _video_model

    except Exception as cnn_err:
        print(f"[Mental-H] Both video model backends failed: {cnn_err}")
        traceback.print_exc()
        return None


def _get_audio_model():
    """Lazy-load the audio emotion Random Forest model."""
    global _audio_model
    if _audio_model is not None:
        return _audio_model
    try:
        import joblib
        if AUDIO_MODEL_DIR not in sys.path:
            sys.path.insert(0, AUDIO_MODEL_DIR)

        model_path = os.path.join(AUDIO_MODEL_DIR, "Emotion_Model.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Audio model not found: {model_path}")

        model = joblib.load(model_path)
        _audio_model = {
            "model": model,
            "emotions": ["Fear", "Angry", "Disgust", "Happy", "Neutral", "Sad", "Surprise"],
        }
        print("[Mental-H] Audio emotion model loaded ✅")
        return _audio_model
    except Exception as e:
        print(f"[Mental-H] Audio model load error: {e}")
        traceback.print_exc()
        return None


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _load_static_recommendations(file_path: str) -> dict:
    """Load static fallback recommendations JSON."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f).get("base_phrases", {})
    except Exception:
        return {}


def _static_rec_for_emotion(emotion: str, source: str = "video") -> list[str]:
    """Static recommendations — used only when personalisation engine fails."""
    rec_file = VIDEO_REC_FILE if source == "video" else AUDIO_REC_FILE
    data = _load_static_recommendations(rec_file)
    key_map = {
        "angry": "angry", "disgust": "disgusted", "fear": "fearful",
        "happy": "happy", "neutral": "neutral", "sad": "sad", "surprise": "surprised",
    }
    key = key_map.get(emotion.lower(), emotion.lower())
    return data.get(key, ["Take care of yourself. Your wellbeing matters."])


def _get_recommendations(db: Session, user_id: int, emotion: str, source: str = "video"):
    """
    Get personalised recommendations + context dict.

    Falls back to static JSON list if the personalisation module errors.
    """
    try:
        if MENTAL_H_DIR not in sys.path:
            sys.path.insert(0, MENTAL_H_DIR)

        from personalized_recommendations import get_personalized_recommendations  # noqa
        recs, ctx = get_personalized_recommendations(db, user_id, emotion, n=3)
        return recs, ctx
    except Exception as pe:
        print(f"[Mental-H] Personalization error (falling back): {pe}")
        return _static_rec_for_emotion(emotion, source), {}


# ─────────────────────────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _save_analysis(
    db: Session,
    user_id: int,
    emotion: str,
    confidence: float,
    source: str,
    *,
    faces_detected: int = 0,
    tone: str | None = None,
    energy: str | None = None,
    rec_index: int = 0,
):
    entry = MentalHealthAnalysis(
        user_id=user_id,
        emotion=emotion,
        confidence=confidence,
        source=source,
        faces_detected=faces_detected if source == "video" else None,
        tone=tone if source == "audio" else None,
        energy=energy if source == "audio" else None,
        rec_shown_index=rec_index,
    )
    db.add(entry)
    db.commit()


def _get_last_emotion(db: Session, user_id: int, source: str = "video") -> str | None:
    entry = (
        db.query(MentalHealthAnalysis)
        .filter(
            MentalHealthAnalysis.user_id == user_id,
            MentalHealthAnalysis.source == source,
        )
        .order_by(desc(MentalHealthAnalysis.timestamp))
        .first()
    )
    return entry.emotion if entry else None


def _compute_stress(db: Session, user_id: int, window: int = 20) -> dict:
    entries = (
        db.query(MentalHealthAnalysis)
        .filter(MentalHealthAnalysis.user_id == user_id)
        .order_by(desc(MentalHealthAnalysis.timestamp))
        .limit(window)
        .all()
    )
    if not entries:
        return {"stress_probability": 0.0, "stress_level": "Low", "emotions_analyzed": 0}

    emotions = [e.emotion.lower() for e in entries if e.emotion]
    if not emotions:
        return {"stress_probability": 0.0, "stress_level": "Low", "emotions_analyzed": 0}

    stress_count = sum(1 for e in emotions if e in STRESS_EMOTIONS)
    prob = stress_count / len(emotions)
    level = "High" if prob >= 0.6 else "Moderate" if prob >= 0.3 else "Low"

    return {
        "stress_probability": round(prob, 2),
        "stress_level": level,
        "emotions_analyzed": len(emotions),
        "stress_emotions_count": stress_count,
    }


def _get_history(db: Session, user_id: int, source: str = "video", limit: int = 50) -> list[dict]:
    entries = (
        db.query(MentalHealthAnalysis)
        .filter(
            MentalHealthAnalysis.user_id == user_id,
            MentalHealthAnalysis.source == source,
        )
        .order_by(desc(MentalHealthAnalysis.timestamp))
        .limit(limit)
        .all()
    )
    return [
        {
            "timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "emotion": e.emotion,
            "confidence": e.confidence,
        }
        for e in reversed(entries)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO PROCESSING: FER BACKEND
# ─────────────────────────────────────────────────────────────────────────────

def _predict_video_fer(cap, detector, total_frames: int, fps: int) -> dict:
    """
    Process video using FER (MTCNN-based) emotion detector with rotation-resilience.
    """
    import cv2
    import datetime

    LOG_PATH = os.path.join(os.getcwd(), "mental_health_debug.log")

    def _log(msg):
        with open(LOG_PATH, "a") as f:
            f.write(f"[{datetime.datetime.now()}] {msg}\n")
        print(msg)

    if MENTAL_H_DIR not in sys.path:
        sys.path.insert(0, MENTAL_H_DIR)

    from video_preprocessor import get_smart_frame_indices, enhance_frame, is_frame_blurry

    frame_indices = get_smart_frame_indices(total_frames, fps=fps, target_samples=60) # Reduced samples for speed

    emotion_accumulator: dict[str, float] = {e: 0.0 for e in EMOTION_CLASSES}
    frame_snapshots: list[dict] = []
    total_weight: float = 0.0
    frames_with_face: int = 0

    # Debug counters
    dbg_read_fail = 0
    dbg_blur_skip = 0
    dbg_no_face   = 0
    dbg_low_conf  = 0
    dbg_fer_error = 0
    dbg_total     = len(frame_indices)
    
    # Rotation tracking
    best_rotation = 0 # 0, 90, 180, 270
    rotation_locked = False

    _log(f"--- FER Pipeline Start (v2.2 - Robust) ---")
    _log(f"Processing {dbg_total} sampled frames...")

    for i, (frame_idx, temporal_weight) in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame_raw = cap.read()
        if not ret:
            dbg_read_fail += 1
            continue

        # Log stats for the first frame
        if i == 0:
            h, w = frame_raw.shape[:2]
            brightness = np.mean(frame_raw)
            _log(f"  First Frame Info: {w}x{h}, mean_brightness={brightness:.1f}")
            if brightness < 5:
                _log("  WARNING: Frame is very dark or black. Decoding might be failing.")

        # Handle Rotation
        work_frame = frame_raw
        if rotation_locked and best_rotation != 0:
            if best_rotation == 90: work_frame = cv2.rotate(frame_raw, cv2.ROTATE_90_CLOCKWISE)
            elif best_rotation == 180: work_frame = cv2.rotate(frame_raw, cv2.ROTATE_180)
            elif best_rotation == 270: work_frame = cv2.rotate(frame_raw, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Resize for performance (MTCNN likes ~640px)
        h, w = work_frame.shape[:2]
        if w > 640:
            scale = 640 / w
            work_frame = cv2.resize(work_frame, (640, int(h * scale)))

        # Blur check
        if is_frame_blurry(work_frame, threshold=25.0):
            dbg_blur_skip += 1
            continue

        # Try detection
        def _try_detect(img):
            try:
                return detector.detect_emotions(img)
            except:
                return None

        # 1. Try with current rotation (raw then enhanced)
        results = _try_detect(work_frame)
        if not results:
            results = _try_detect(enhance_frame(work_frame))

        # 2. If no face and rotation not locked, try other rotations (only for first 5 frames to find best)
        if not results and not rotation_locked and i < 5:
            for rot in [90, 180, 270]:
                if rot == 90: test_frame = cv2.rotate(frame_raw, cv2.ROTATE_90_CLOCKWISE)
                elif rot == 180: test_frame = cv2.rotate(frame_raw, cv2.ROTATE_180)
                elif rot == 270: test_frame = cv2.rotate(frame_raw, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
                # Resize test frame
                th, tw = test_frame.shape[:2]
                if tw > 640:
                    ts = 640 / tw
                    test_frame = cv2.resize(test_frame, (640, int(th * ts)))
                
                results = _try_detect(test_frame)
                if not results: results = _try_detect(enhance_frame(test_frame))
                
                if results:
                    best_rotation = rot
                    rotation_locked = True
                    work_frame = test_frame
                    _log(f"  Rotation detected and locked at {rot} degrees!")
                    break

        if not results:
            dbg_no_face += 1
            continue

        # Lock rotation on any success
        if not rotation_locked:
            rotation_locked = True
            _log(f"  Rotation confirmed at {best_rotation} degrees.")

        # Use the largest detected face
        largest = max(results, key=lambda r: r["box"][2] * r["box"][3])
        raw_scores: dict = largest["emotions"]
        max_prob = max(raw_scores.values())

        if max_prob < 0.10: # Extra low threshold for real-world robustness
            dbg_low_conf += 1
            continue

        for emo_raw, prob in raw_scores.items():
            emo_key = emo_raw.capitalize()
            if emo_key in emotion_accumulator:
                emotion_accumulator[emo_key] += prob * temporal_weight

        total_weight    += temporal_weight
        frames_with_face += 1

        dominant_this_frame = max(raw_scores, key=raw_scores.get).capitalize()
        frame_snapshots.append({
            "frame": frame_idx,
            "time_sec": round(frame_idx / fps, 1) if fps > 0 else 0,
            "emotion": dominant_this_frame,
            "confidence": round(max_prob, 2),
            "all_emotions": {k.capitalize(): round(v, 3) for k, v in raw_scores.items()},
        })

    _log(f"FER Final: {frames_with_face} faces found | read_fail={dbg_read_fail} blur={dbg_blur_skip} no_face={dbg_no_face} low_conf={dbg_low_conf} / {dbg_total} total")

    return {
        "accumulator": emotion_accumulator,
        "total_weight": total_weight,
        "frames_with_face": frames_with_face,
        "frame_snapshots": frame_snapshots,
    }


def _predict_video_cnn(cap, model_data: dict, total_frames: int, fps: int) -> dict:
    """
    Fallback: original CNN model with improved frame sampling & preprocessing.
    """
    import cv2
    import torch
    from PIL import Image

    if MENTAL_H_DIR not in sys.path:
        sys.path.insert(0, MENTAL_H_DIR)

    from video_preprocessor import get_smart_frame_indices, enhance_frame, is_frame_blurry

    model     = model_data["model"]
    transform = model_data["transform"]
    device    = model_data["device"]

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    frame_indices = get_smart_frame_indices(total_frames, fps=fps, target_samples=80)

    emotion_accumulator: dict[str, float] = {e: 0.0 for e in EMOTION_CLASSES}
    frame_snapshots: list[dict] = []
    total_weight: float = 0.0
    frames_with_face: int = 0

    for frame_idx, temporal_weight in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue

        if is_frame_blurry(frame, threshold=60.0):
            continue

        frame = enhance_frame(frame)
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(30, 30))

        if len(faces) == 0:
            continue

        largest_face = max(faces, key=lambda r: r[2] * r[3])
        x, y, fw, fh = largest_face
        face_crop = frame[y: y + fh, x: x + fw]

        if face_crop.size == 0:
            continue

        face_pil = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
        tensor   = transform(face_pil).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(tensor)
            probs  = torch.softmax(output, dim=1)[0]

        probs_list = probs.cpu().numpy().tolist()

        if max(probs_list) < 0.30:
            continue

        for i, emo in enumerate(EMOTION_CLASSES):
            emotion_accumulator[emo] += probs_list[i] * temporal_weight

        total_weight    += temporal_weight
        frames_with_face += 1

        dom_idx = int(probs.argmax().item())
        frame_snapshots.append({
            "frame":      frame_idx,
            "time_sec":   round(frame_idx / fps, 1) if fps > 0 else 0,
            "emotion":    EMOTION_CLASSES[dom_idx],
            "confidence": round(probs_list[dom_idx], 2),
        })

    return {
        "accumulator":      emotion_accumulator,
        "total_weight":     total_weight,
        "frames_with_face": frames_with_face,
        "frame_snapshots":  frame_snapshots,
    }


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────────────────────────────────
class FrameAnalysisRequest(BaseModel):
    image_base64: str


class AudioAnalysisRequest(BaseModel):
    audio_base64: str
    filename: Optional[str] = "upload.wav"


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status")
def get_status():
    """Check module status and model availability."""
    fer_available = False
    try:
        # fer v25+ moved FER class to fer.fer submodule
        try:
            from fer.fer import FER  # noqa
        except ImportError:
            from fer import FER  # noqa — older versions
        fer_available = True
    except ImportError:
        pass

    return {
        "status": "Module Active",
        "video_model_available": (
            fer_available or
            os.path.exists(os.path.join(MENTAL_H_DIR, "emotion_model.pth"))
        ),
        "video_backend": "fer+mtcnn" if fer_available else "cnn",
        "audio_model_available": os.path.exists(os.path.join(AUDIO_MODEL_DIR, "Emotion_Model.pkl")),
        "personalized_recommendations": True,
        "features": [
            "face_emotion_detection",
            "audio_emotion_detection",
            "stress_prediction",
            "personalized_recommendations",
        ],
    }


# ── /predict/face ─────────────────────────────────────────────────────────────
@router.post("/predict/face")
def predict_face_emotion(
    request: FrameAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predict emotion from a base64-encoded face image."""
    try:
        import cv2
        from PIL import Image

        model_data = _get_video_model()
        if model_data is None:
            raise HTTPException(status_code=503, detail="Video emotion model not available")

        # Decode image
        try:
            img_bytes = base64.b64decode(request.image_base64)
            img_pil   = Image.open(BytesIO(img_bytes)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        img_np = np.array(img_pil)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        emotion, confidence, faces_found = "Neutral", 0.5, 0

        # ── FER backend ──
        if model_data["backend"] == "fer":
            detector = model_data["detector"]

            if MENTAL_H_DIR not in sys.path:
                sys.path.insert(0, MENTAL_H_DIR)
            from video_preprocessor import enhance_frame
            img_bgr = enhance_frame(img_bgr)

            results = detector.detect_emotions(img_bgr)
            if results:
                largest = max(results, key=lambda r: r["box"][2] * r["box"][3])
                raw     = largest["emotions"]
                emotion    = max(raw, key=raw.get).capitalize()
                confidence = float(max(raw.values()))
                faces_found = len(results)
            else:
                # No face — run on whole image
                result_full = detector.detect_emotions(img_bgr)
                if result_full:
                    raw     = result_full[0]["emotions"]
                    emotion    = max(raw, key=raw.get).capitalize()
                    confidence = float(max(raw.values()))

        # ── CNN fallback backend ──
        else:
            import torch
            model     = model_data["model"]
            transform = model_data["transform"]
            device    = model_data["device"]

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            gray  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                x, y, fw, fh = max(faces, key=lambda r: r[2] * r[3])
                face_crop = img_pil.crop((x, y, x + fw, y + fh))
                faces_found = len(faces)
            else:
                face_crop = img_pil

            tensor = transform(face_crop).unsqueeze(0).to(device)
            with torch.no_grad():
                out   = model(tensor)
                probs = torch.softmax(out, dim=1)[0]
                idx   = probs.argmax().item()
            emotion    = EMOTION_CLASSES[idx]
            confidence = float(probs[idx])

        recs, ctx = _get_recommendations(db, current_user.id, emotion, "video")
        _save_analysis(db, current_user.id, emotion, confidence, "video",
                       faces_detected=faces_found, rec_index=ctx.get("rotation_used", 0))

        return {
            "emotion":        emotion,
            "confidence":     round(confidence, 2),
            "faces_detected": faces_found,
            "recommendations": recs,
            "rec_context":     ctx,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Mental-H] Face prediction error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── /predict/audio ─────────────────────────────────────────────────────────────
@router.post("/predict/audio")
async def predict_audio_emotion(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predict emotion from an uploaded audio file."""
    try:
        model_data = _get_audio_model()
        if model_data is None:
            raise HTTPException(status_code=503, detail="Audio emotion model not available")

        model        = model_data["model"]
        emotions_list = model_data["emotions"]

        if AUDIO_MODEL_DIR not in sys.path:
            sys.path.insert(0, AUDIO_MODEL_DIR)
        import Audio_feature_extraction as Afe

        os.makedirs("temp", exist_ok=True)
        temp_path = f"temp/{uuid.uuid4()}_{audio.filename}"

        try:
            contents = await audio.read()
            with open(temp_path, "wb") as f:
                f.write(contents)

            import librosa
            from moviepy.editor import AudioFileClip

            # Use MoviePy to convert to WAV (MoviePy has its own ffmpeg)
            audio_clip = AudioFileClip(temp_path)
            temp_wav = temp_path + ".wav"
            
            try:
                audio_clip.write_audiofile(temp_wav, codec='pcm_s16le', verbose=False, logger=None)
                audio_clip.close()
                
                # IMPORTANT: Resample to 24414Hz to match training dataset
                # librosa.load with sr=None keeps native, which breaks features if not 24414Hz
                waveform, sample_rate = librosa.load(temp_wav, sr=24414)
                
                # Normalize volume (peak normalization)
                if len(waveform) > 0:
                    peak = np.max(np.abs(waveform))
                    if peak > 0:
                        waveform = waveform / peak
                
                # Cleanup temp wav immediately
                if os.path.exists(temp_wav):
                    try: os.remove(temp_wav)
                    except: pass
            finally:
                try: audio_clip.close()
                except: pass
            
            chroma   = Afe.feature_chromagram(waveform, sample_rate)
            mel      = Afe.feature_melspectrogram(waveform, sample_rate)
            mfcc     = Afe.feature_mfcc(waveform, sample_rate)
            features = np.hstack((chroma, mel, mfcc))

            # Raw prediction
            prediction = model.predict([features])
            pred_idx   = int(prediction[0]) - 1
            
            # CRITICAL: Corrected mapping to match training folder order:
            # ['angry', 'disgust', 'Fear', 'happy', 'neutral', 'sad', 'surprise']
            corrected_mapping = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]
            
            pred_emotion = (
                corrected_mapping[pred_idx]
                if 0 <= pred_idx < len(corrected_mapping)
                else "Neutral"
            )

            confidence = 0.0
            if hasattr(model, "predict_proba"):
                try:
                    confidence = float(np.max(model.predict_proba([features])))
                except Exception:
                    confidence = 0.75

            mfcc_mean = float(np.mean(mfcc))
            mel_mean  = float(np.mean(mel))
            tone   = "Bright" if mfcc_mean > 0 else "Steady" if mfcc_mean > -5 else "Deep"
            energy = "High"   if mel_mean  > 0.5 else "Moderate" if mel_mean > 0.2 else "Low"

            recs, ctx = _get_recommendations(db, current_user.id, pred_emotion, "audio")
            _save_analysis(db, current_user.id, pred_emotion, confidence, "audio",
                           tone=tone, energy=energy, rec_index=ctx.get("rotation_used", 0))

            return {
                "emotion":     pred_emotion,
                "confidence":  round(confidence, 2),
                "tone":        tone,
                "energy":      energy,
                "recommendations": recs,
                "rec_context":     ctx,
            }

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Mental-H] Audio prediction error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── /predict/video ─────────────────────────────────────────────────────────────
@router.post("/predict/video")
async def predict_video_emotion(
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Predict emotion from an uploaded video file.

    Uses FER (MTCNN) with CLAHE preprocessing and temporal-weighted
    frame sampling.  Falls back to the original CNN if FER is unavailable.
    """
    try:
        import cv2

        model_data = _get_video_model()
        if model_data is None:
            raise HTTPException(status_code=503, detail="Video emotion model not available")

        os.makedirs("temp", exist_ok=True)
        temp_path = f"temp/{uuid.uuid4()}_{video.filename}"

        try:
            contents = await video.read()
            with open(temp_path, "wb") as f:
                f.write(contents)

            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="Cannot open video file. Ensure it is a valid format.")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps          = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            duration_sec = round(total_frames / fps, 1) if fps > 0 else 0.0

            log_msg = f"[Mental-H] Video Upload: {total_frames} frames @ {fps} fps ({duration_sec}s) | file={video.filename} | backend={model_data['backend']}"
            print(log_msg)
            with open("mental_health_debug.log", "a") as f:
                import datetime
                f.write(f"[{datetime.datetime.now()}] {log_msg}\n")

            # ── Run the appropriate backend pipeline ─────────────────────────
            if model_data["backend"] == "fer":
                result = _predict_video_fer(cap, model_data["detector"], total_frames, fps)
            else:
                result = _predict_video_cnn(cap, model_data, total_frames, fps)

            cap.release()

            accumulator      = result["accumulator"]
            total_weight     = result["total_weight"]
            frames_with_face = result["frames_with_face"]
            frame_snapshots  = result["frame_snapshots"]

            # ── Handle zero-face case ─────────────────────────────────────
            if frames_with_face == 0 or total_weight == 0:
                return {
                    "emotion":          "Unknown",
                    "confidence":       0.0,
                    "faces_detected":   0,
                    "total_frames":     total_frames,
                    "frames_analyzed":  0,
                    "duration_sec":     duration_sec,
                    "emotion_breakdown": {},
                    "frame_results":    [],
                    "note":             "No clear faces detected. Try a well-lit, front-facing video.",
                    "recommendations":  ["Upload a well-lit video with your face clearly visible.",
                                         "Avoid dark environments or covering your face.",
                                         "Look directly at the camera for best results."],
                    "rec_context":      {},
                }

            # ── Normalise accumulated scores ─────────────────────────────
            normalised = {e: v / total_weight for e, v in accumulator.items()}
            total_norm = sum(normalised.values())

            dominant_emotion   = max(normalised, key=normalised.get)
            dominant_score     = normalised[dominant_emotion]
            # Calibrated confidence: dominant share of total probability mass
            cal_confidence     = dominant_score / total_norm if total_norm > 0 else 0.0
            display_confidence = min(0.99, cal_confidence)

            confidence_label = (
                "High"   if display_confidence >= 0.70 else
                "Medium" if display_confidence >= 0.45 else
                "Low"
            )

            # Emotion breakdown using per-frame dominant counts for display
            raw_counts = Counter(s["emotion"] for s in frame_snapshots)
            total_det  = sum(raw_counts.values())
            emotion_breakdown = {
                emo: {
                    "count": cnt,
                    "percentage": round(cnt / total_det * 100, 1),
                    "weighted_score": round(normalised.get(emo, 0.0), 3),
                }
                for emo, cnt in raw_counts.most_common()
            }

            # Video quality ratio
            quality_ratio = frames_with_face / max(1, len(result["frame_snapshots"]) + 1)

            # ── Personalised recommendations ────────────────────────────
            recs, ctx = _get_recommendations(db, current_user.id, dominant_emotion, "video")

            # ── Save to DB ──────────────────────────────────────────────
            _save_analysis(
                db, current_user.id, dominant_emotion, display_confidence, "video",
                faces_detected=total_det,
                rec_index=ctx.get("rotation_used", 0),
            )

            return {
                "emotion":           dominant_emotion,
                "confidence":        round(display_confidence, 2),
                "confidence_label":  confidence_label,
                "faces_detected":    total_det,
                "total_frames":      total_frames,
                "frames_analyzed":   frames_with_face,
                "duration_sec":      duration_sec,
                "video_quality":     round(min(1.0, quality_ratio), 2),
                "backend_used":      model_data["backend"],
                "emotion_breakdown": emotion_breakdown,
                "frame_results":     frame_snapshots[-50:],
                "recommendations":   recs,
                "rec_context":       ctx,
            }

        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Mental-H] Video prediction error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── /last-emotion ──────────────────────────────────────────────────────────────
@router.get("/last-emotion")
def get_last_emotion(
    source: str = "video",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the most recent emotion for this user and source."""
    emotion = _get_last_emotion(db, current_user.id, source)
    if emotion is None:
        return {"has_previous": False, "emotion": None, "recommendations": [], "rec_context": {}}

    recs, ctx = _get_recommendations(db, current_user.id, emotion, source)
    return {
        "has_previous":    True,
        "emotion":         emotion,
        "recommendations": recs,
        "rec_context":     ctx,
    }


# ── /stress ────────────────────────────────────────────────────────────────────
@router.get("/stress")
def get_stress_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return stress analysis from recent emotion history."""
    stress_data = _compute_stress(db, current_user.id)
    history     = _get_history(db, current_user.id, limit=50)

    # Rolling stress trend (window of 6)
    stress_trend = []
    window_size  = 6
    if len(history) >= window_size:
        for i in range(window_size, len(history) + 1):
            window = history[i - window_size: i]
            sc     = sum(1 for h in window if h["emotion"] and h["emotion"].lower() in STRESS_EMOTIONS)
            stress_trend.append({
                "index":              i - window_size,
                "stress_probability": round(sc / window_size * 100, 1),
            })

    dominant_emotion = "Unknown"
    if history:
        emotion_counts   = Counter(h["emotion"] for h in history if h["emotion"])
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "Unknown"

    return {
        **stress_data,
        "dominant_emotion": dominant_emotion,
        "stress_trend":     stress_trend,
        "history":          history[-20:],
    }


# ── /history ───────────────────────────────────────────────────────────────────
@router.get("/history")
def get_emotion_history_endpoint(
    source: str = "video",
    limit:  int  = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return paginated emotion history for charts."""
    history = _get_history(db, current_user.id, source, limit)
    return {"source": source, "count": len(history), "history": history}


# ── /recommendations/{emotion} ────────────────────────────────────────────────
@router.get("/recommendations/{emotion}")
def get_recommendations_public(
    emotion: str,
    source:  str = "video",
):
    """Static recommendations for an emotion (no auth — used by demo screens)."""
    recs = _static_rec_for_emotion(emotion, source)
    return {"emotion": emotion, "source": source, "recommendations": recs}
