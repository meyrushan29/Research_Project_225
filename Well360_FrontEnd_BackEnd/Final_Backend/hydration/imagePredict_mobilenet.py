import sys
import os
import time
from datetime import datetime

# ======================================================
# DEPENDENCY HANDLING
# ======================================================
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import models
    from PIL import Image, ImageDraw, ImageFont, ImageStat
    import matplotlib.pyplot as plt
    import numpy as np
    import cv2
    from captum.attr import LayerGradCam
except ImportError as e:
    print(f"[CRITICAL ERROR] Missing Dependency: {e}")

from core.config import DEVICE, MOBILENET_MODEL_OUT
from hydration.preprocess_images import get_transforms

# Import new advanced feature extraction
try:
    from hydration.lip_feature_extractor import (
        extract_all_features,
        calculate_image_quality_score
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"[Warning] Advanced features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False


# ======================================================
# QUALITY CHECKS
# ======================================================
def check_image_quality(image):
    """
    Checks if image is too dark or has low variance (blur/flat).
    Returns (Passed: bool, Reason: str)
    """
    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    
    # 1. Brightness Check
    brightness = stat.mean[0]
    if brightness < 40:  # Threshold for too dark
        return False, f"Image too dark (Brightness: {brightness:.1f}/255)"
    
    # 2. Blur/Contrast Check (Variance)
    variance = stat.var[0]
    if variance < 100:   # Threshold for low detail
        return False, f"Image likely blurry or low contrast (Variance: {variance:.1f})"
        
    return True, "OK"


# ======================================================
# CONTENT RELEVANCE CHECK (SKIN TONE FILTER)
# ======================================================
def check_content_relevance(image):
    """
    Uses HSV color space to check if image contains sufficient skin-tone pixels.
    Returns (Passed: bool, Reason: str)
    """
    # Convert PIL Image to NumPy array (RGB)
    img_np = np.array(image)
    
    try:
        from matplotlib.colors import rgb_to_hsv
        img_hsv = rgb_to_hsv(img_np / 255.0) # Normalized 0-1
        
        # Ranges for Skin (Normalized 0-1)
        h = img_hsv[:,:,0]
        s = img_hsv[:,:,1]
        v = img_hsv[:,:,2]
        
        # Skin Mask
        # Skin is typically red-yellow. H near 0.
        skin_mask = ( ((h < 0.14) | (h > 0.95)) & (s > 0.20) & (s < 0.70) & (v > 0.35) )
        
        skin_pixels = np.sum(skin_mask)
        total_pixels = image.width * image.height
        ratio = skin_pixels / total_pixels
        
        if ratio < 0.15: # 15% threshold
            return False, f"No human skin/lips detected (Skin Ratio: {ratio:.1%})"
            
        return True, "OK"

    except Exception as e:
        # Fallback if validation fails (don't block app)
        print(f"[Warning] Content Check Skipped: {e}")
        return True, "Check Skipped"


# ======================================================
# LOAD TRAINED MOBILENETV2 MODEL (IMPROVED ARCHITECTURE)
# ======================================================
class ImprovedLipModel(nn.Module):
    """Enhanced MobileNetV2 architecture matching the training script"""
    def __init__(self, num_classes=2):
        super().__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=False)
        num_ftrs = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_ftrs, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.4),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        return self.mobilenet(x)

def load_model(class_names):
    if not os.path.exists(MOBILENET_MODEL_OUT):
        print(f"Model file not found at: {MOBILENET_MODEL_OUT}")

    model = ImprovedLipModel(num_classes=len(class_names))

    try:
        model.load_state_dict(
            torch.load(MOBILENET_MODEL_OUT, map_location=DEVICE)
        )
    except Exception as e:
        print(f"Failed to load model weights: {e}")

    model.to(DEVICE)
    model.eval()
    return model


# ======================================================
# RECOMMENDATION LOGIC
# ======================================================
def get_recommendation(label_status, confidence):
    if label_status == "Dehydrate":
        return (
            "⚠️ Possible Dehydration Detected.\n"
            f"   (Confidence: {confidence:.0%})\n"
            "- Drink 1–2 glasses of water immediately.\n"
            "- Avoid caffeine/alcohol for 2 hours.\n"
            "- Check if lips feel dry or cracked."
        )
    elif label_status == "Uncertain":
        return (
            "⚠️ Results Inconclusive.\n"
            "- The model is not confident.\n"
            "- Please try again with better lighting."
        )
    elif label_status == "REJECTED":
        return (
            "❌ Prediction Aborted.\n"
            "- The image does not appear to contain a human face/lips.\n"
            "- Please use a clear close-up of the lip area."
        )
    else:
        return (
            "✅ Hydration appears normal.\n"
            "- Keep maintaining regular water intake."
        )


# ======================================================
# HYDRATION SCORE (0–100)
# ======================================================
def calculate_hydration_score(label, confidence):
    if label == "Dehydrate":
        # Lower score = Worse hydration
        return int((1 - confidence) * 50) + 10
    else:
        # Higher score = Better hydration
        return int(60 + confidence * 40)


# ======================================================
# UI OVERLAY
# ======================================================
def draw_overlay(image, score, status, warnings=[]):
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Colors
    if status == "Dehydrate":
        bg_col = (200, 50, 50, 180) # Red
    elif status == "Uncertain":
        bg_col = (200, 160, 50, 180) # Orange
    elif status == "REJECTED":
        bg_col = (80, 80, 80, 200) # Gray
    else:
        bg_col = (50, 180, 80, 180) # Green

    # Top Banner
    draw.rectangle((0, 0, image.width, 60), fill=bg_col)
    
    # Try to load font, fallback to default
    try:
        font_lg = ImageFont.truetype("arial.ttf", 26)
        font_sm = ImageFont.truetype("arial.ttf", 16)
    except:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    draw.text((20, 15), f"Status: {status}", fill="white", font=font_lg)

    # Warnings (if any)
    y_warn = 70
    for w in warnings:
        draw.rectangle((0, y_warn, image.width, y_warn + 30), fill=(0, 0, 0, 150))
        draw.text((20, y_warn + 5), f"⚠️ {w}", fill="yellow", font=font_sm)
        y_warn += 35

    return Image.alpha_composite(image, overlay).convert("RGB")



# ======================================================
# GRAD-CAM VISUALIZATION (XAI)
# ======================================================
def generate_gradcam_heatmap(model, input_tensor, target_class, original_image):
    """
    Generates a Grad-CAM heatmap overlay and a textual explanation.
    Returns (heatmap_pil, explanation_text)
    """
    try:
        # Target the last conv layer of MobileNetV2
        target_layer = model.mobilenet.features[18]
        lgc = LayerGradCam(model, target_layer)
        
        # Attribute
        atttribution = lgc.attribute(input_tensor, target=target_class, relu_attributions=True)
        
        # Process heatmap
        heatmap = atttribution.squeeze().cpu().detach().numpy()
        heatmap = np.maximum(heatmap, 0)
        
        # Explain based on heatmap distribution
        # Split into 3x3 grid to find hot zones
        h, w = heatmap.shape
        grid_y, grid_x = h // 3, w // 3
        
        regions = {
            "top": np.mean(heatmap[0:grid_y, :]),
            "bottom": np.mean(heatmap[2*grid_y:, :]),
            "left": np.mean(heatmap[:, 0:grid_x]),
            "right": np.mean(heatmap[:, 2*grid_x:]),
            "center": np.mean(heatmap[grid_y:2*grid_y, grid_x:2*grid_x])
        }
        
        # Find highest region
        top_region = max(regions, key=regions.get)
        
        if regions[top_region] < 0.01:
            explanation = "The AI looked at the overall lip texture to determine hydration."
        else:
            region_map = {
                "top": "upper lip area",
                "bottom": "lower lip area",
                "left": "left corner of the mouth",
                "right": "right corner of the mouth",
                "center": "central lip region"
            }
            explanation = f"The AI focused primarily on the {region_map[top_region]}, identifying specific texture patterns associated with your hydration level."

        # Normalize for image
        if np.max(heatmap) > 0:
            heatmap /= np.max(heatmap)
            
        # Resize to match original image
        overlay_heatmap = cv2.resize(heatmap, (original_image.width, original_image.height))
        overlay_heatmap = np.uint8(255 * overlay_heatmap)
        
        # Apply colormap (JET)
        heatmap_img = cv2.applyColorMap(overlay_heatmap, cv2.COLORMAP_JET)
        heatmap_img = cv2.cvtColor(heatmap_img, cv2.COLOR_BGR2RGB)
        
        # Overlay on original image
        original_np = np.array(original_image)
        overlay = cv2.addWeighted(original_np, 0.6, heatmap_img, 0.4, 0)
        
        return Image.fromarray(overlay), explanation
    except Exception as e:
        print(f"[XAI Error] Grad-CAM failed: {e}")
        return None, "Reasoning visualization unavailable."

# ======================================================
# IMAGE PREDICTION (ENHANCED WITH ADVANCED FEATURES)
# ======================================================
def predict_image(image_path, model, class_names):
    transform = get_transforms(train=False)
    
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"[Error] Could not open image: {e}")
        return None

    warnings = []
    advanced_info = {}
    
    # ========== ADVANCED FEATURE EXTRACTION ==========
    if ADVANCED_FEATURES_AVAILABLE:
        try:
            print("[INFO] Running advanced feature extraction...")
            feature_data = extract_all_features(image, auto_enhance=True)
            
            features = feature_data['features']
            processed_image = feature_data['processed_image']
            enhanced_image = feature_data['enhanced_image']
            landmarks = feature_data['landmarks']
            metadata = feature_data['metadata']
            
            # Calculate quality score
            quality_score = calculate_image_quality_score(features)
            
            # Store advanced info for output
            advanced_info = {
                'quality_score': quality_score,
                'lip_detected': features.get('lip_detected', False),
                'crack_severity': features.get('crack_severity_score', 0),
                'color_redness': features.get('redness_ratio', 0),
                'texture_roughness': features.get('surface_roughness', 0),
                'landmarks': landmarks
            }
            
            # Quality-based warnings
            if quality_score < 60:
                warnings.append(f"Image Quality: {quality_score:.0f}/100")
            
            if not features.get('lip_detected'):
                warnings.append("Lip region not clearly detected")
            
            # Use processed (cropped + enhanced) image for prediction
            image_for_prediction = processed_image
            
            print(f"[INFO] Quality Score: {quality_score:.1f}/100")
            print(f"[INFO] Lip Detected: {features.get('lip_detected')}")
            print(f"[INFO] Crack Severity: {features.get('crack_severity_score', 0):.1f}")
            
        except Exception as e:
            print(f"[Warning] Advanced features failed: {e}")
            image_for_prediction = image
    else:
        image_for_prediction = image
    
    # 1. Quality Check (Original)
    is_good, reason = check_image_quality(image)
    if not is_good:
        print(f"[Warning] Image Quality Issue: {reason}")
        warnings.append(reason)

    # 2. Content Relevance Check (Skin Filter)
    is_relevant, relevance_reason = check_content_relevance(image_for_prediction)
    if not is_relevant:
        print(f"[REJECTING] {relevance_reason}")
        # Stop Pipeline Here
        status_display = "REJECTED"
        warnings.append(relevance_reason)
        score = 0
        final_image = draw_overlay(image, score, status_display, warnings)
        
        # Save & Return Early
        os.makedirs("img/uploads", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"img/uploads/rejected_{ts}.png"
        final_image.save(out_path)
        
        return status_display, 0, 0.0, get_recommendation("REJECTED", 0), out_path, None, "Image rejected due to quality issues", advanced_info

    # 3. Inference (Only if relevant)
    tensor = transform(image_for_prediction).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        outputs = model(tensor)
        probs = F.softmax(outputs, dim=1)
        
    p_dehydrate = probs[0][0].item()
    p_normal = probs[0][1].item()
    
    # ========== ENHANCED DECISION LOGIC ==========
    # Combine ML prediction with advanced features
    DEHYDRATION_THRESHOLD = 0.35
    UNCERTAINTY_THRESHOLD = 0.65
    
    # Adjust threshold based on advanced features
    if ADVANCED_FEATURES_AVAILABLE and 'crack_severity' in advanced_info:
        crack_severity = advanced_info['crack_severity']
        
        # If high crack severity detected, boost dehydration confidence
        if crack_severity > 30:
            print(f"[INFO] High crack severity ({crack_severity:.1f}) detected - adjusting prediction")
            p_dehydrate = min(1.0, p_dehydrate + 0.15)  # Boost dehydration probability
            p_normal = 1.0 - p_dehydrate

    if p_dehydrate > DEHYDRATION_THRESHOLD:
        label = "Dehydrate"
        confidence = p_dehydrate
    else:
        label = "Normal"
        confidence = p_normal

    if confidence < UNCERTAINTY_THRESHOLD:
        status_display = "Uncertain"
        warnings.append("Low Confidence")
    else:
        status_display = label

    score = calculate_hydration_score(label, confidence)
    
    # 🔥 XAI: Generate Heatmap & Explanation
    heatmap_pil, xai_desc = generate_gradcam_heatmap(model, tensor, class_names.index(label), image_for_prediction)
    
    # Enhance XAI description with advanced features
    if ADVANCED_FEATURES_AVAILABLE and advanced_info:
        xai_additions = []
        if advanced_info.get('crack_severity', 0) > 20:
            xai_additions.append(f"Surface texture analysis detected signs of dryness (severity: {advanced_info['crack_severity']:.0f}/100).")
        if advanced_info.get('color_redness', 0) > 0.1:
            xai_additions.append("Color analysis shows increased redness typical of dehydration.")
        
        if xai_additions:
            xai_desc = xai_desc + " " + " ".join(xai_additions)
    
    final_image = draw_overlay(image, score, status_display, warnings)
    
    os.makedirs("img/uploads", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save standard result
    out_path = f"img/uploads/result_{ts}.png"
    final_image.save(out_path)
    
    # Save heatmap version
    xai_path = f"img/uploads/xai_heatmap_{ts}.png"
    if heatmap_pil:
        heatmap_pil.save(xai_path)
    else:
        xai_path = None

    return status_display, score, confidence, get_recommendation(status_display, confidence), out_path, xai_path, xai_desc, advanced_info



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

    result = predict_image(image_path, GLOBAL_MODEL, GLOBAL_CLASSES)
    
    # Handle both old and new return formats
    if len(result) == 8:
        label, score, conf, rec, saved_path, xai_path, xai_desc, advanced_info = result
    else:
        # Fallback for old format
        label, score, conf, rec, saved_path = result[:5]
        xai_path = result[5] if len(result) > 5 else None
        xai_desc = result[6] if len(result) > 6 else "No description"
        advanced_info = {}
    
    return {
        "prediction": label,
        "hydration_score": score,
        "confidence": float(conf),
        "saved_image_path": saved_path,
        "xai_heatmap_path": xai_path,
        "xai_description": xai_desc,
        "recommendation": rec,
        "advanced_analysis": {
            "quality_score": advanced_info.get('quality_score', None),
            "lip_detected": advanced_info.get('lip_detected', None),
            "crack_severity": advanced_info.get('crack_severity', None),
            "texture_roughness": advanced_info.get('texture_roughness', None)
        }
    }
