import sys
import os
import time
from datetime import datetime

# ======================================================
# DEPENDENCIES
# ======================================================
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import models
    from PIL import Image, ImageDraw, ImageFont, ImageStat
    import numpy as np
    import cv2
    from captum.attr import LayerGradCam
except ImportError as e:
    print(f"[CRITICAL] Missing: {e}")

from core.config import DEVICE, MOBILENET_MODEL_OUT
from hydration.training.preprocess_images import get_transforms


# ======================================================
# STEP 1 — DETECT & CROP LIP SHAPE
# ======================================================
LIP_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,
             409, 270, 269, 267, 0, 37, 39, 40, 185]

def _detect_lip_mediapipe(image_rgb_np):
    """Try lip detection using MediaPipe face mesh. Works on full face photos."""
    try:
        import mediapipe as mp
        h, w = image_rgb_np.shape[:2]
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.3
        )
        res = face_mesh.process(image_rgb_np)
        face_mesh.close()

        if not res.multi_face_landmarks:
            return None, False

        lm = res.multi_face_landmarks[0]
        pts = np.array([(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h))
                        for i in LIP_OUTER], dtype=np.int32)
        x, y, bw, bh = cv2.boundingRect(pts)

        # 8% padding
        px, py = max(4, int(bw * 0.08)), max(4, int(bh * 0.08))
        x1, y1 = max(0, x - px), max(0, y - py)
        x2, y2 = min(w, x + bw + px), min(h, y + bh + py)

        crop = Image.fromarray(image_rgb_np[y1:y2, x1:x2])
        if crop.width < 15 or crop.height < 10:
            return None, False
        return crop, True
    except Exception as e:
        print(f"[MediaPipe Error] {e}")
        return None, False


def _crop_center_fallback(image_rgb_np):
    """
    Center string crop fallback for close-up lip photos where MediaPipe fails.
    Keeps center 70% width, lower 65% height.
    This safely crops out most mustache/chin areas.
    """
    h, w = image_rgb_np.shape[:2]
    cx = int(w * 0.15)
    cy = int(h * 0.15)
    crop_np = image_rgb_np[cy:h, cx:w - cx]
    return Image.fromarray(crop_np)


def detect_lip_shape(image):
    """
    STEP 1: Detect lip shape and crop.
    
    Strategy EXACTLY mirrors training data preprocessing:
    1. Try MediaPipe FaceMesh (for photos with nose/chin visible)
    2. Center-strip crop fallback (for tight lip shots)
    No color segmentation is used (avoids dark skin / facial hair bugs).
    """
    img_np = np.array(image)

    # 1. MediaPipe
    crop, ok = _detect_lip_mediapipe(img_np)
    if ok:
        print(f"[STEP 1] MediaPipe crop — {crop.width}x{crop.height}")
        return crop, "mediapipe"

    # 2. Center fallback
    crop = _crop_center_fallback(img_np)
    print(f"[STEP 1] Center-crop fallback — {crop.width}x{crop.height}")
    return crop, "center_crop"


# ======================================================
# QUALITY & CONTENT CHECKS
# ======================================================
def check_image_quality(image):
    stat = ImageStat.Stat(image.convert("L"))
    b, v = stat.mean[0], stat.var[0]
    if b < 15: return False, "Too dark"
    if b > 250: return False, "Too bright"
    if v < 20: return False, "Too blurry"
    return True, "OK"


# ======================================================
# MODEL ARCHITECTURES
# ======================================================
class SimpleLipModel(nn.Module):
    def __init__(self, n=2):
        super().__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=False)
        f = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(f, n))
    def forward(self, x): return self.mobilenet(x)

class ImprovedLipModel(nn.Module):
    def __init__(self, n=2):
        super().__init__()
        # Pretrained MUST be False here for loading dict without ImageNet weights overriding
        self.mobilenet = models.mobilenet_v2(pretrained=False)
        f = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.3), nn.Linear(f, 512), nn.ReLU(), nn.BatchNorm1d(512),
            nn.Dropout(0.4), nn.Linear(512, 256), nn.ReLU(), nn.BatchNorm1d(256),
            nn.Dropout(0.3), nn.Linear(256, n))
    def forward(self, x): return self.mobilenet(x)

class ExpertLipModel(nn.Module):
    def __init__(self, n=2):
        super().__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=False)
        f = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.3), nn.Linear(f, 512), nn.ReLU(), nn.BatchNorm1d(512),
            nn.Dropout(0.4), nn.Linear(512, 256), nn.ReLU(), nn.BatchNorm1d(256),
            nn.Dropout(0.3), nn.Linear(256, 128), nn.ReLU(), nn.BatchNorm1d(128),
            nn.Dropout(0.2), nn.Linear(128, n))
    def forward(self, x): return self.mobilenet(x)


def load_model(class_names):
    if not os.path.exists(MOBILENET_MODEL_OUT):
        raise FileNotFoundError(f"Model not found: {MOBILENET_MODEL_OUT}")
    nc = len(class_names)
    try:
        try:
            sd = torch.load(MOBILENET_MODEL_OUT, map_location=DEVICE, weights_only=True)
        except TypeError:
            sd = torch.load(MOBILENET_MODEL_OUT, map_location=DEVICE)
        
        # Determine model structure from shape
        w1  = sd.get("mobilenet.classifier.1.weight")
        w9  = sd.get("mobilenet.classifier.9.weight")
        w13 = sd.get("mobilenet.classifier.13.weight")
        
        if w1 is not None and w1.shape == (nc, 1280):
            model = SimpleLipModel(nc); print("[OK] SimpleLipModel structure")
        elif w13 is not None and w13.shape[0] == nc:
            model = ExpertLipModel(nc); print("[OK] ExpertLipModel structure")
        else:
            # Fallback is ImprovedLipModel
            model = ImprovedLipModel(nc); print("[OK] ImprovedLipModel structure")
            
        model.load_state_dict(sd, strict=False)
        print(f"[OK] Loaded: {MOBILENET_MODEL_OUT}")
    except Exception as e:
        raise RuntimeError(f"Load failed: {e}") from e
    model.to(DEVICE).eval()
    return model


# ======================================================
# HANDCRAFTED FEATURES (ROBUSTNESS)
# ======================================================
def extract_lip_features(image_pil):
    """
    Extracts hydration features that are robust to skin tone/facial hair.
    Returns: crack_score, color_score
    """
    img_bgr = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Vertical crack lines (Sobel Y edge density)
    sobel_x = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_x = np.absolute(sobel_x)
    sobel_x = np.uint8(255 * sobel_x / np.max(sobel_x))
    crack_pixels = np.sum(sobel_x > 100)
    crack_score = min(1.0, crack_pixels / (img_gray.shape[0] * img_gray.shape[1] * 0.15))
    
    # 2. Pink/Red vs Pale/Gray ratio (Color dryness)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    
    # Low saturation = pale/gray (dry signal)
    pale_pixels = np.sum(s_channel < 50)
    total_pixels = img_gray.shape[0] * img_gray.shape[1]
    color_dryness = min(1.0, pale_pixels / (total_pixels * 0.3))
    
    return crack_score, color_dryness


# ======================================================
# HELPERS
# ======================================================
def get_recommendation(status, confidence):
    recs = {
        "Dehydrate": f"Possible Dehydration Detected (Confidence: {confidence:.0%}).\n- Drink 1-2 glasses of water.\n- Avoid caffeine for 2 hours.",
        "Uncertain": "Results Inconclusive.\n- Try again with a clear photo.",
        "REJECTED": "Image rejected.\n- Please take a clear close-up.",
        "Normal": "Hydration appears normal.\n- Keep maintaining regular water intake."
    }
    return recs.get(status, recs["Normal"])

def calculate_hydration_score(label, expected_dehy):
    # Scale from final probability
    if expected_dehy > 0.5:
        return max(10, min(45, int((1 - expected_dehy) * 50) + 10))
    return max(60, min(95, int(55 + (1-expected_dehy) * 40)))

def draw_overlay(image, score, status, warnings=[]):
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    colors = {"Dehydrate": (200,50,50,180), "Uncertain": (200,160,50,180), "REJECTED": (80,80,80,200)}
    draw.rectangle((0, 0, image.width, 60), fill=colors.get(status, (50,180,80,180)))
    try: font = ImageFont.truetype("arial.ttf", 26); sfont = ImageFont.truetype("arial.ttf", 16)
    except: font = ImageFont.load_default(); sfont = font
    draw.text((20, 15), f"Status: {status}", fill="white", font=font)
    y = 70
    for w in warnings:
        draw.rectangle((0, y, image.width, y+30), fill=(0,0,0,150))
        draw.text((20, y+5), w, fill="yellow", font=sfont)
        y += 35
    return Image.alpha_composite(image, overlay).convert("RGB")


# ======================================================
# GRAD-CAM
# ======================================================
def generate_gradcam_heatmap(model, tensor, target_class, original_image):
    try:
        layer = model.mobilenet.features[18]
        if 'LayerGradCam' not in globals():
            return None, "XAI unobtainable."
        lgc = LayerGradCam(model, layer)
        attr = lgc.attribute(tensor, target=target_class, relu_attributions=True)
        hm = attr.squeeze().cpu().detach().numpy()
        hm = np.maximum(hm, 0)
        if np.max(hm) > 0: hm /= np.max(hm)
        
        hm_r = cv2.resize(hm, (original_image.width, original_image.height))
        hm_c = cv2.applyColorMap(np.uint8(255 * hm_r), cv2.COLORMAP_JET)
        hm_c = cv2.cvtColor(hm_c, cv2.COLOR_BGR2RGB)
        blended = cv2.addWeighted(np.array(original_image), 0.6, hm_c, 0.4, 0)
        return Image.fromarray(blended), "AI texture analysis heatmap."
    except Exception as e:
        print(f"[XAI] {e}")
        return None, "Visualization unavailable."


# ======================================================
# MAIN PIPELINE — HYBRID APPROACH
# ======================================================
def predict_image(image_path, model, class_names):
    """
    1. Try MediaPipe, else center crop
    2. Extract handcrafted features (cracks, color dryness)
    3. Run CNN inference
    4. Ensemble (CNN 70% + Features 30%)
    """
    transform = get_transforms(train=False)

    try: image = Image.open(image_path).convert("RGB")
    except Exception: return None

    warnings = []

    # ── STEP 1: DETECT LIP SHAPE ──
    print("=" * 50)
    lip_crop, method = detect_lip_shape(image)

    # ── STEP 2: QUALITY CHECK ──
    ok, reason = check_image_quality(lip_crop)
    if not ok: warnings.append(reason)

    # ── STEP 3: CNN INFERENCE ──
    tensor = transform(lip_crop).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        outputs = model(tensor)
        probs = F.softmax(outputs, dim=1)

    cnn_dehy = probs[0][0].item()
    cnn_norm = probs[0][1].item()
    
    # ── STEP 4: RULE-BASED FEATURES ──
    # This prevents total failure on out-of-distribution skin tones
    crack_score, color_dryness = extract_lip_features(lip_crop)
    feature_dehy = (crack_score * 0.6) + (color_dryness * 0.4)
    
    print(f"[STEP 3] CNN Dehydrate = {cnn_dehy:.4f}")
    print(f"[STEP 4] Features Dehydrate = {feature_dehy:.4f} (Cracks: {crack_score:.2f}, Pale: {color_dryness:.2f})")

    # ── STEP 5: ENSEMBLE DECISION ──
    # Blend CNN output (learning) with handcrafted features (robustness)
    final_dehy = (cnn_dehy * 0.7) + (feature_dehy * 0.3)
    
    if final_dehy > 0.50:
        label, confidence = "Dehydrate", final_dehy
    else:
        label, confidence = "Normal", 1.0 - final_dehy

    status = label if confidence >= 0.55 else "Uncertain"
    if status == "Uncertain": warnings.append(f"Low Confidence ({confidence:.0%})")

    score = calculate_hydration_score(label, final_dehy)
    print(f"[STEP 5] {status} | Final Score: {score}/100 | Confidence: {confidence:.0%}")
    print("=" * 50)

    # ── STEP 6: HEATMAP ──
    heatmap, xai_desc = generate_gradcam_heatmap(model, tensor, 0 if label=="Dehydrate" else 1, lip_crop)

    # ── SAVE ──
    final = draw_overlay(image, score, status, warnings)
    os.makedirs("img/uploads", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"img/uploads/result_{ts}.png"
    final.save(out_path)
    xai_path = None
    if heatmap:
        xai_path = f"img/uploads/xai_heatmap_{ts}.png"
        heatmap.save(xai_path)

    adv = {"lip_detected": method == "mediapipe", "quality_score": 70 if ok else 40}
    return status, score, confidence, get_recommendation(status, confidence), out_path, xai_path, xai_desc, adv


# ======================================================
# ENTRY POINT
# ======================================================
GLOBAL_MODEL = None
GLOBAL_CLASSES = ["Dehydrate", "Normal"]

def predict_single(image_path):
    global GLOBAL_MODEL
    if GLOBAL_MODEL is None:
        try:
            GLOBAL_MODEL = load_model(GLOBAL_CLASSES)
        except Exception as e:
            return {"error": str(e), "confidence": 0, "hydration_score": 0, "prediction": "Error"}

    result = predict_image(image_path, GLOBAL_MODEL, GLOBAL_CLASSES)
    if result is None:
        return {"error": "Failed", "confidence": 0, "hydration_score": 0, "prediction": "Error"}

    label, score, conf, rec, saved, xai, desc, adv = result if len(result) == 8 else (*result[:5], None, "", {})

    return {
        "prediction": label,
        "hydration_score": score,
        "confidence": float(conf),
        "saved_image_path": saved,
        "xai_heatmap_path": xai,
        "xai_description": desc,
        "recommendation": rec,
        "advanced_analysis": {
            "quality_score": adv.get("quality_score"),
            "lip_detected": adv.get("lip_detected"),
        }
    }
