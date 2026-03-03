# ======================================================
# PREDICTION ACCURACY CONFIGURATION
# ======================================================
# Adjust these parameters to improve prediction accuracy
# based on your specific use case and video quality

class PredictionConfig:
    """
    Configuration for fitness exercise prediction accuracy
    """
    
    # ============================================================
    # CONFIDENCE THRESHOLDS
    # ============================================================
    # Minimum confidence to accept a prediction (0-100%)
    # Higher = More strict, fewer false positives but may miss some exercises
    # Lower = More lenient, may include false positives
    # Minimum confidence to accept a prediction (0-100%)
    # ↑ Raised: filters out low-quality noisy frame predictions
    MIN_CONFIDENCE = 50.0
    
    # Confidence needed to BREAK an established lock (must be very high)
    HIGH_CONFIDENCE = 88.0
    
    # Confidence levels for display
    CONFIDENCE_LOW    = 45.0
    CONFIDENCE_MEDIUM = 70.0
    CONFIDENCE_HIGH   = 85.0
    
    # ============================================================
    # TEMPORAL SMOOTHING
    # ============================================================
    # NOTE: With FRAME_SKIP=2 in api_handler.py, effective FPS is halved.
    # These values are in EFFECTIVE frames (after skipping).
    # 20 effective frames ≈ 40 real frames ≈ ~1.3s at 30fps
    HISTORY_WINDOW = 20
    
    # Skip initial frames (warm-up period) — noisy early frames ignored
    WARMUP_FRAMES = 10  # 10 effective frames ≈ ~0.7s real-time
    
    # ============================================================
    # EXERCISE LOCKING MECHANISM
    # ============================================================
    # Frames needed with majority agreement to lock the exercise
    LOCK_THRESHOLD = 18  # Needs 18 consecutive-window frames agreeing
    
    # Percentage agreement needed within window to lock (0.0-1.0)
    LOCK_AGREEMENT = 0.80  # 80% — very strict lock-on
    
    # How much to erode lock per contradicting high-conf frame
    # Lower = lock is harder to break (more stable display)
    LOCK_EROSION_RATE = 2
    
    # ============================================================
    # PREDICTION FILTERING
    # ============================================================
    # Minimum number of effective frames with valid pose to accept video
    MIN_VALID_FRAMES = 5  # Fewer needed since we're sampling frames
    
    # Minimum video duration in seconds to process
    MIN_VIDEO_DURATION = 2.0
    
    # Maximum acceptable "unknown" percentage in predictions
    MAX_UNKNOWN_PERCENT = 0.45  # Slightly more lenient
    
    # ============================================================
    # SIMILAR EXERCISE GROUPS
    # ============================================================
    # Exercises that are commonly confused - use higher thresholds
    SIMILAR_EXERCISE_GROUPS = [
        # Bicep exercises
        ["barbell_biceps_curl", "hammer_curl"],
        
        # Push exercises
        ["push_up", "bench_press", "incline_bench_press"],
        
        # Deadlift variations
        ["deadlift", "romanian_deadlift"],
        
        # Tricep exercises
        ["tricep_dips", "tricep_pushdown"],
        
        # Shoulder exercises
        ["shoulder_press", "lateral_raise"],
        
        # Leg exercises
        ["squat", "leg_extension"],
        
        # Back exercises
        ["pull_up", "lat_pulldown", "t_bar_row"],

        # Setup Confusions (Standing with bar)
        ["barbell_biceps_curl", "deadlift"],
    ]
    
    # ============================================================
    # FORM DETECTION
    # ============================================================
    # Minimum confidence to determine form (correct/wrong)
    FORM_MIN_CONFIDENCE = 45.0
    
    # Weight given to form prediction vs exercise prediction
    FORM_WEIGHT = 0.8  # 80% importance
    
    # ============================================================
    # VIDEO QUALITY DETECTION
    # ============================================================
    # Detect low quality videos and warn user
    LOW_QUALITY_THRESHOLDS = {
        "avg_confidence": 50.0,  # Average confidence below this = low quality
        "valid_frame_ratio": 0.6,  # Less than 60% valid frames = low quality
        "stable_exercise_ratio": 0.7,  # Less than 70% same exercise = unstable
    }
    
    # ============================================================
    # DISPLAY SETTINGS
    # ============================================================
    # Show debug information in video overlay
    DEBUG_MODE = False
    
    # Show confidence bars in output video
    SHOW_CONFIDENCE_BARS = True
    
    # Show top 3 predictions instead of just top 1
    SHOW_TOP_PREDICTIONS = False


# ======================================================
# EXERCISE SIMILARITY MATRIX
# ======================================================
# Define which exercises are similar (for better filtering)
def get_exercise_similarity(exercise1, exercise2):
    """
    Check if two exercises are similar and might be confused
    Returns: float (0.0 = completely different, 1.0 = very similar)
    """
    for group in PredictionConfig.SIMILAR_EXERCISE_GROUPS:
        if exercise1 in group and exercise2 in group:
            return 0.8  # Highly similar
    
    # Check if they use the same muscle groups
    from fitness.exercise_config import EXERCISE_CONFIG
    
    if exercise1 in EXERCISE_CONFIG and exercise2 in EXERCISE_CONFIG:
        joints1 = set(EXERCISE_CONFIG[exercise1]["joints"])
        joints2 = set(EXERCISE_CONFIG[exercise2]["joints"])
        
        # Calculate Jaccard similarity
        if len(joints1 | joints2) > 0:
            similarity = len(joints1 & joints2) / len(joints1 | joints2)
            return similarity
    
    return 0.0  # Not similar


# ======================================================
# QUALITY METRICS
# ======================================================
class QualityMetrics:
    """Track video quality metrics for better user feedback"""
    
    @staticmethod
    def assess_video_quality(predictions, total_frames, valid_frames):
        """
        Assess overall video quality based on prediction metrics
        Returns: dict with quality assessment
        """
        if total_frames == 0:
            return {"quality": "unknown", "issues": ["No frames processed"]}
        
        valid_ratio = valid_frames / total_frames
        issues = []
        
        # Check valid frame ratio
        if valid_ratio < PredictionConfig.LOW_QUALITY_THRESHOLDS["valid_frame_ratio"]:
            issues.append(f"Low pose detection rate ({valid_ratio*100:.1f}%)")
        
        # Check prediction confidence
        if predictions:
            avg_conf = sum(p[2] for p in predictions) / len(predictions)
            if avg_conf < PredictionConfig.LOW_QUALITY_THRESHOLDS["avg_confidence"]:
                issues.append(f"Low average confidence ({avg_conf:.1f}%)")
        
        # Determine overall quality
        if len(issues) == 0:
            quality = "high"
        elif len(issues) == 1:
            quality = "medium"
        else:
            quality = "low"
        
        return {
            "quality": quality,
            "valid_frame_ratio": valid_ratio,
            "issues": issues,
            "recommendations": QualityMetrics.get_recommendations(issues)
        }
    
    @staticmethod
    def get_recommendations(issues):
        """Get recommendations based on quality issues"""
        recommendations = []
        
        for issue in issues:
            if "pose detection" in issue.lower():
                recommendations.append("Ensure you're fully visible in the frame")
                recommendations.append("Use better lighting")
                recommendations.append("Position camera to capture your full body")
            
            if "confidence" in issue.lower():
                recommendations.append("Hold poses more clearly at start and end of movement")
                recommendations.append("Record from a more stable angle")
                recommendations.append("Ensure clear view of joints (no obstruction)")
        
        return recommendations if recommendations else ["Video quality is good!"]
