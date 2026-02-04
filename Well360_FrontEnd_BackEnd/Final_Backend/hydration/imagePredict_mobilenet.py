import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

from core.config import DEVICE, MOBILENET_MODEL_OUT
from hydration.preprocess_images import get_transforms
from core.utils import calculate_unified_score


# ======================================================
# LOAD TRAINED MOBILENETV2 MODEL
# ======================================================
def load_model(class_names):
    model = models.mobilenet_v2(pretrained=False)

    num_ftrs = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Linear(num_ftrs, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, len(class_names))
    )

    model.load_state_dict(
        torch.load(MOBILENET_MODEL_OUT, map_location=DEVICE)
    )
    model.to(DEVICE)
    model.eval()
    return model


# ======================================================
# RECOMMENDATION LOGIC
# ======================================================
def get_recommendation(label):
    if label == "Dehydrate":
        return (
            "Possible dehydration detected.\n"
            "- Drink 1–2 glasses of water immediately\n"
            "- Avoid heavy physical activity\n"
            "- Avoid caffeine & alcohol\n"
            "- Monitor urine color\n"
            "- Seek medical advice if symptoms persist"
        )
    else:
        return (
            "Hydration level appears normal.\n"
            "- Maintain regular water intake\n"
            "- Stay hydrated during exercise"
        )


# ======================================================
# HYDRATION SCORE (0–100)
# ======================================================
# calculate_hydration_score REMOVED - using utils.calculate_unified_score


# ======================================================
# FONT SAFE LOADER
# ======================================================
def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()


# ======================================================
# UI OVERLAY
# ======================================================
def draw_hydration_score(image, score):
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    title_font = load_font(24)
    text_font = load_font(18)

    if score < 40:
        bg, bar, status = (220, 60, 60, 150), (200, 40, 40, 220), "Dehydrated"
    elif score < 70:
        bg, bar, status = (240, 170, 60, 150), (220, 140, 40, 220), "Moderate"
    else:
        bg, bar, status = (60, 160, 90, 150), (40, 130, 70, 220), "Normal"

    x1, y1, x2, y2 = 15, 15, 360, 150
    draw.rectangle((x1, y1, x2, y2), fill=bg)

    draw.text((x1 + 15, y1 + 10), "Hydration Status", fill="white", font=title_font)
    draw.text((x1 + 15, y1 + 50), f"Score: {score}/100", fill="white", font=text_font)
    draw.text((x1 + 15, y1 + 75), f"Status: {status}", fill="white", font=text_font)

    bar_x1, bar_y1, bar_x2 = x1 + 15, y1 + 110, x2 - 15
    draw.rectangle((bar_x1, bar_y1, bar_x2, bar_y1 + 14), fill=(255, 255, 255, 90))

    fill = int((score / 100) * (bar_x2 - bar_x1))
    draw.rectangle((bar_x1, bar_y1, bar_x1 + fill, bar_y1 + 14), fill=bar)

    return Image.alpha_composite(image, overlay).convert("RGB")


# ======================================================
# IMAGE SELECTION FROM TERMINAL
# ======================================================
def select_image_from_terminal():
    images = [f for f in os.listdir(".") if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    if not images:
        raise FileNotFoundError("No images found in current directory")

    print("\nAvailable Images:")
    for i, img in enumerate(images, 1):
        print(f"{i}. {img}")

    choice = input("\nSelect image number (default 1): ").strip()
    return images[int(choice) - 1] if choice.isdigit() else images[0]


# ======================================================
# IMAGE VALIDATION (MEDIAPIPE FACE MESH)
# ======================================================
try:
    import mediapipe as mp
    try:
        # standard import
        mp_solutions = mp.solutions
    except AttributeError:
        # fallback for some windows envs
        import mediapipe.python.solutions as mp_solutions
    
    HAS_MEDIAPIPE = True
except ImportError as e:
    HAS_MEDIAPIPE = False
    print(f"Warning: MediaPipe not found ({e}). Lip validation/cropping disabled.")

def is_likely_skin(image, threshold=0.3):
    """
    Checks if image has significant skin-tone like pixels (YCbCr).
    Threshold can be increased for stricter checks (e.g. macro shots).
    """
    try:
        img_ycbcr = image.convert('YCbCr')
        ycbcr_data = np.array(img_ycbcr)
        
        # Extract channels
        cb = ycbcr_data[:, :, 1]
        cr = ycbcr_data[:, :, 2]
        
        # Skin color range in YCbCr (approximate for general skin/lips)
        # Cb: 77-127, Cr: 133-173 (Face/Lip range)
        mask = (cb >= 77) & (cb <= 127) & (cr >= 133) & (cr <= 173)
        
        skin_pixels = np.sum(mask)
        total_pixels = mask.size
        ratio = skin_pixels / total_pixels
        
        # print(f"DEBUG: Skin Ratio: {ratio:.2f}") # Uncomment for debug
        
        if ratio > threshold: 
            return True
        return False
    except Exception as e:
        print(f"Skin check error: {e}")
        return False

def validate_and_crop_lips(image):
    """
    Validates image using MediaPipe Face Mesh.
    If a face is found, CROPS the image to the lip area with padding.
    Returns: (is_valid, image_or_error_msg)
    """
    # 1. Blur Check
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    variance = ImageStat.Stat(edges).var[0]
    
    if variance < 50: 
        return False, "Image too blurry. Please focus."

    # Fallback if MediaPipe is broken
    if not HAS_MEDIAPIPE:
        # Fallback to simple skin check
        if is_likely_skin(image):
             return True, image
        return False, "MediaPipe is missing. Cannot validate lips. Please check server configuration."

    # 2. MediaPipe Face Mesh Detection
    mp_face_mesh = mp_solutions.face_mesh
    img_np = np.array(image)
    
    try:
        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        ) as face_mesh:
            results = face_mesh.process(img_np)
            
            if not results.multi_face_landmarks:
                # SPECIAL HANDLING FOR MACRO SHOTS
                # Use Skin Tone Heuristic (Stricter Threshold for fallback)
                if is_likely_skin(image, threshold=0.55):
                    print("Info: No full face detected, but dominant skin tone found. Assuming Macro Lip Shot.")
                    return True, image
                else:
                    return False, "No lips detected. Please ensure the image contains a clear face/lips."
                
            # 3. Intelligent Cropping (Only if full face found)
            face_landmarks = results.multi_face_landmarks[0]
            h, w, _ = img_np.shape
            
            # Indices for lips
            lip_indices = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
            
            x_coords = [int(face_landmarks.landmark[i].x * w) for i in lip_indices]
            y_coords = [int(face_landmarks.landmark[i].y * h) for i in lip_indices]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            # Add Padding (20%)
            pad_x = int((max_x - min_x) * 0.2)
            pad_y = int((max_y - min_y) * 0.4) 
            
            crop_x1 = max(0, min_x - pad_x)
            crop_y1 = max(0, min_y - pad_y)
            crop_x2 = min(w, max_x + pad_x)
            crop_y2 = min(h, max_y + pad_y)
            
            cropped_image = image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            
            return True, cropped_image
    except Exception as e:
        print(f"MediaPipe error: {e}")
        return False, f"Validation error: {str(e)}" # Fail safely instead of returning unverified image


# ======================================================
# IMAGE PREDICTION
# ======================================================
def predict_image(image_path, model, class_names):
    transform = get_transforms(train=False)
    image = Image.open(image_path).convert("RGB")

    # VALIDATE & CROP FIRST
    is_valid, result = validate_and_crop_lips(image)
    if not is_valid:
        # result is error message
        return "Error", 0, 0.0, result, None
    
    # result is cropped image
    image = result.convert("RGB")

    tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(tensor)
        probs = F.softmax(outputs, dim=1)
        pred = probs.argmax(dim=1).item()

    label = class_names[pred]
    confidence = probs[0][pred].item()
    score = calculate_unified_score('lip', label, confidence)

    final_image = draw_hydration_score(image, score)

    os.makedirs("img", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"img/result_{timestamp}.png"
    final_image.save(out_path)

    # plt.imshow(final_image)
    # plt.axis("off")
    # plt.title(f"{label} | Score: {score}/100")
    # plt.show()

    return label, score, confidence, get_recommendation(label), out_path


# ======================================================
# LAZY LOADER GLOBAL
# ======================================================
GLOBAL_MODEL = None
GLOBAL_CLASSES = ["Dehydrate", "Normal"]

def predict_single(image_path):
    global GLOBAL_MODEL
    if GLOBAL_MODEL is None:
        try:
            GLOBAL_MODEL = load_model(GLOBAL_CLASSES)
        except Exception as e:
            return {"error": f"Model load failed: {str(e)}", "confidence": 0, "hydration_score": 0, "prediction": "Error"}

    label, score, conf, rec, saved_path = predict_image(image_path, GLOBAL_MODEL, GLOBAL_CLASSES)
    
    return {
        "prediction": label,
        "hydration_score": score,
        "confidence": float(conf),
        "saved_image_path": saved_path,
        "recommendation": rec
    }

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    class_names = ["Dehydrate", "Normal"]  # MUST match training

    model = load_model(class_names)
    image_path = select_image_from_terminal()

    label, score, conf, rec, saved = predict_image(
        image_path, model, class_names
    )

    print("\n" + "=" * 60)
    print(f"Prediction      : {label}")
    print(f"Hydration Score : {score}/100")
    print(f"Confidence      : {conf:.2f}")
    print(f"Saved Image     : {saved}")
    print("\nRecommendation:\n" + rec)
    print("=" * 60)
