"""
Advanced Feature Extraction for Lip Hydration Analysis
Extracts multi-modal features: texture, color, spatial patterns

NOTE: This is used for SUPPLEMENTARY analysis only.
The CNN model makes the primary prediction.
These features provide additional signals (crack severity, redness, etc.)
"""
import numpy as np
import cv2
from PIL import Image
from skimage.feature import local_binary_pattern


# ======================================================
# 1. LIP REGION DETECTION & CROPPING
# ======================================================
def detect_and_crop_lips(image):
    """
    Detect lip region from image.
    
    Since training data is already lip-area crops,
    this does a CLEAN tight crop (no black masking) if face is found.
    If no face found (already a lip crop), returns image as-is.
    
    Returns (cropped_image, success_flag, landmarks)
    """
    try:
        import mediapipe as mp
        
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        img_np = np.array(image)
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            img_rgb = img_np
        else:
            img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        
        results = face_mesh.process(img_rgb)
        face_mesh.close()
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            h, w = img_rgb.shape[:2]
            
            # Outer lip indices for crop boundary
            lip_outer_indices = [
                61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,
                409, 270, 269, 267, 0, 37, 39, 40, 185
            ]
            
            # Get bounding box from outer lip
            lip_points = np.array([
                (int(landmarks.landmark[i].x * w), int(landmarks.landmark[i].y * h))
                for i in lip_outer_indices
            ], dtype=np.int32)
            
            x, y, bw, bh = cv2.boundingRect(lip_points)
            
            # Small padding (5% of lip size)
            pad_x = max(3, int(bw * 0.05))
            pad_y = max(3, int(bh * 0.05))
            
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(w, x + bw + pad_x)
            y2 = min(h, y + bh + pad_y)
            
            # CLEAN crop — no black masking
            cropped = image.crop((x1, y1, x2, y2))
            
            lip_coords = [
                (landmarks.landmark[i].x * w - x1,
                 landmarks.landmark[i].y * h - y1)
                for i in lip_outer_indices
            ]
            
            return cropped, True, lip_coords
        
        # No face found — image is likely already a lip crop
        return image, False, None
        
    except ImportError:
        return image, False, None
    except Exception as e:
        print(f"[Warning] Lip detection failed: {e}")
        return image, False, None


# ======================================================
# 2. COLOR FEATURE EXTRACTION
# ======================================================
def extract_color_features(image):
    """Extract color statistics from multiple color spaces."""
    img_np = np.array(image)
    
    img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
    img_lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
    
    rgb_mean = np.mean(img_np, axis=(0, 1))
    rgb_std = np.std(img_np, axis=(0, 1))
    hsv_mean = np.mean(img_hsv, axis=(0, 1))
    lab_mean = np.mean(img_lab, axis=(0, 1))
    
    # Redness Ratio
    r = img_np[:, :, 0].astype(float)
    g = img_np[:, :, 1].astype(float)
    b = img_np[:, :, 2].astype(float)
    redness = (r - (g + b) / 2) / (r + g + b + 1e-6)
    redness_score = np.mean(redness)
    
    color_variance = np.mean([np.var(img_np[:, :, i]) for i in range(3)])
    
    return {
        'rgb_mean_r': float(rgb_mean[0]),
        'rgb_mean_g': float(rgb_mean[1]),
        'rgb_mean_b': float(rgb_mean[2]),
        'rgb_std': float(np.mean(rgb_std)),
        'hsv_hue': float(hsv_mean[0]),
        'hsv_saturation': float(hsv_mean[1]),
        'hsv_value': float(hsv_mean[2]),
        'lab_lightness': float(lab_mean[0]),
        'lab_a': float(lab_mean[1]),
        'lab_b': float(lab_mean[2]),
        'redness_ratio': float(redness_score),
        'color_uniformity': float(1.0 / (color_variance + 1))
    }


# ======================================================
# 3. TEXTURE ANALYSIS (CRACK & DRYNESS DETECTION)
# ======================================================
def analyze_lip_texture(image):
    """
    Detect cracks, roughness, and dry patches.
    
    IMPORTANT: Crack severity is calibrated so that:
    - Normal hydrated lips: 0-30
    - Mildly dry lips: 30-50
    - Clearly cracked/dehydrated lips: 50-100
    """
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # 1. Edge Detection (cracks show as fine strong edges)
    # Use higher thresholds to avoid false positives from skin texture
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    
    # 2. Texture Variance using Laplacian
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_var = np.var(laplacian)
    laplacian_mean = np.abs(np.mean(laplacian))
    
    # 3. Local Binary Pattern
    lbp = local_binary_pattern(gray, P=8, R=1, method='uniform')
    lbp_hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10), density=True)
    
    # 4. Gradient Magnitude
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
    gradient_mean = np.mean(gradient_magnitude)
    
    # 5. Surface roughness
    local_std = cv2.blur(gray, (5, 5))
    texture_roughness = np.std(local_std)
    
    # Crack severity score (0-100) — CALIBRATED
    # Normal lips: edge_density ~0.02-0.05, gradient_mean ~10-25
    # Dry/cracked lips: edge_density ~0.08-0.15, gradient_mean ~30-60
    # 
    # Formula: scale edge_density (0-0.15 range) and gradient (0-60 range) 
    # to 0-100, weighted 60/40
    edge_component = min(60, (edge_density / 0.15) * 60)
    gradient_component = min(40, (gradient_mean / 60) * 40)
    crack_score = edge_component + gradient_component
    
    return {
        'crack_density': float(edge_density),
        'crack_severity_score': float(crack_score),
        'surface_roughness': float(laplacian_var),
        'texture_strength': float(gradient_mean),
        'texture_variation': float(texture_roughness),
        'lbp_entropy': float(-np.sum(lbp_hist * np.log(lbp_hist + 1e-10))),
        'edge_sharpness': float(laplacian_mean)
    }


# ======================================================
# 4. AUTOMATIC IMAGE ENHANCEMENT
# ======================================================
def auto_adjust_image(image):
    """
    Light enhancement for feature extraction.
    Only CLAHE on lightness — no double-enhancing.
    """
    img_np = np.array(image)
    
    # Use LAB color space — enhance L channel only
    lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    
    # CLAHE only (no equalizeHist — that was causing over-processing)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    
    enhanced = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2RGB)
    
    return Image.fromarray(enhanced)


# ======================================================
# 5. COMBINED FEATURE EXTRACTION
# ======================================================
def extract_all_features(image, auto_enhance=True):
    """
    Main feature extraction pipeline.
    Returns dict with all features + metadata.
    """
    original_image = image
    if auto_enhance:
        image = auto_adjust_image(image)
    
    # Detect and crop lips (clean crop, no masking)
    cropped_image, lip_detected, landmarks = detect_and_crop_lips(image)
    
    # Extract features from cropped region
    color_features = extract_color_features(cropped_image)
    texture_features = analyze_lip_texture(cropped_image)
    
    all_features = {
        **color_features,
        **texture_features,
        'lip_detected': lip_detected,
        'image_enhanced': auto_enhance,
        'crop_success': lip_detected
    }
    
    return {
        'features': all_features,
        'processed_image': cropped_image,
        'enhanced_image': image if auto_enhance else original_image,
        'landmarks': landmarks,
        'metadata': {
            'original_size': original_image.size,
            'processed_size': cropped_image.size,
            'lip_region_detected': lip_detected
        }
    }


# ======================================================
# 6. FEATURE-BASED QUALITY SCORE
# ======================================================
def calculate_image_quality_score(features):
    """Calculate overall image quality score (0-100)."""
    score = 100.0
    
    if not features.get('lip_detected', False):
        score -= 30
    
    lightness = features.get('lab_lightness', 128)
    if lightness < 50:
        score -= 20
    elif lightness > 230:
        score -= 15
    
    uniformity = features.get('color_uniformity', 0.5)
    if uniformity < 0.3:
        score -= 10
    
    texture_strength = features.get('texture_strength', 10)
    if texture_strength < 5:
        score -= 15
    
    return max(0, min(100, score))
