# ======================================================
# FITNESS XAI EXPLAINER
# Generates natural language explanations for AI decisions
# ======================================================

import numpy as np

# MediaPipe landmark names (33 landmarks)
LANDMARK_NAMES = [
    "Nose", "Left Eye Inner", "Left Eye", "Left Eye Outer",
    "Right Eye Inner", "Right Eye", "Right Eye Outer",
    "Left Ear", "Right Ear", "Mouth Left", "Mouth Right",
    "Left Shoulder", "Right Shoulder", "Left Elbow", "Right Elbow",
    "Left Wrist", "Right Wrist", "Left Pinky", "Right Pinky",
    "Left Index", "Right Index", "Left Thumb", "Right Thumb",
    "Left Hip", "Right Hip", "Left Knee", "Right Knee",
    "Left Ankle", "Right Ankle", "Left Heel", "Right Heel",
    "Left Foot Index", "Right Foot Index"
]

# Which joints are relevant for each exercise (friendly names)
EXERCISE_KEY_JOINTS = {
    "pull_up":           ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Shoulder", "Left Elbow"],
    "push_up":           ["Right Shoulder", "Right Elbow", "Right Wrist", "Right Hip", "Right Knee"],
    "barbell_biceps_curl": ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Elbow", "Left Wrist"],
    "hammer_curl":       ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Elbow", "Left Wrist"],
    "bench_press":       ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Shoulder", "Left Elbow"],
    "incline_bench_press": ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Shoulder", "Left Elbow"],
    "lat_pulldown":      ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Shoulder", "Left Elbow"],
    "tricep_dips":       ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Shoulder"],
    "tricep_pushdown":   ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Elbow"],
    "shoulder_press":    ["Right Shoulder", "Right Elbow", "Right Wrist", "Left Shoulder", "Left Elbow"],
    "lateral_raise":     ["Right Shoulder", "Right Elbow", "Left Shoulder", "Left Elbow"],
    "t_bar_row":         ["Right Shoulder", "Right Elbow", "Right Wrist", "Right Hip"],
    "squat":             ["Right Hip", "Right Knee", "Right Ankle", "Left Hip", "Left Knee"],
    "deadlift":          ["Right Shoulder", "Right Hip", "Right Knee", "Left Hip"],
    "romanian_deadlift": ["Right Shoulder", "Right Hip", "Right Knee", "Left Hip"],
    "hip_thrust":        ["Right Shoulder", "Right Hip", "Right Knee", "Left Hip"],
    "leg_extension":     ["Right Hip", "Right Knee", "Right Ankle", "Left Knee"],
    "leg_raises":        ["Right Shoulder", "Right Hip", "Right Knee", "Left Hip"],
    "russian_twist":     ["Right Shoulder", "Left Shoulder", "Right Hip", "Left Hip"],
    "plank":             ["Right Shoulder", "Right Hip", "Right Ankle", "Left Shoulder", "Left Hip"],
}

# Exercise-specific form tips (keyed by exercise)
EXERCISE_FORM_TIPS = {
    "squat": {
        "low_rom": "Try to squat deeper — aim for thighs parallel to the ground.",
        "poor_stability": "Keep your core tight and avoid lateral sway during the squat.",
        "good_form": "Great squat depth and controlled movement!"
    },
    "push_up": {
        "low_rom": "Lower your chest closer to the ground for a full range push-up.",
        "poor_stability": "Keep your body in a straight plank position throughout.",
        "good_form": "Excellent push-up form with full range of motion!"
    },
    "barbell_biceps_curl": {
        "low_rom": "Extend your arms fully at the bottom and curl to your shoulders.",
        "poor_stability": "Keep your elbows pinned to your sides — avoid swinging the weight.",
        "good_form": "Clean curls with good elbow control!"
    },
    "hammer_curl": {
        "low_rom": "Bring the weight all the way up and fully extend at the bottom.",
        "poor_stability": "Avoid using momentum — control the weight throughout the curl.",
        "good_form": "Solid hammer curl technique!"
    },
    "bench_press": {
        "low_rom": "Touch the bar to your chest and fully extend at the top.",
        "poor_stability": "Keep your feet firmly planted and avoid lifting your hips off the bench.",
        "good_form": "Great bench press with controlled movement!"
    },
    "deadlift": {
        "low_rom": "Fully extend your hips at the top and hinge properly at the bottom.",
        "poor_stability": "Keep the bar close to your body and your back neutral.",
        "good_form": "Strong deadlift with proper hip hinge pattern!"
    },
    "lat_pulldown": {
        "low_rom": "Pull the bar down to your upper chest and fully extend your arms.",
        "poor_stability": "Avoid leaning too far back — keep your torso upright.",
        "good_form": "Good lat pulldown with full range of motion!"
    },
    "pull_up": {
        "low_rom": "Pull your chin above the bar and fully extend at the bottom.",
        "poor_stability": "Minimize kipping — control the movement without swinging.",
        "good_form": "Impressive pull-up with full range!"
    },
    "shoulder_press": {
        "low_rom": "Press fully overhead and lower to at least ear level.",
        "poor_stability": "Keep your core braced and avoid arching your back excessively.",
        "good_form": "Clean overhead press with good control!"
    },
    "plank": {
        "low_rom": "Maintain a neutral spine — don't let your hips sag or pike up.",
        "poor_stability": "Focus on squeezing your glutes and bracing your core.",
        "good_form": "Excellent plank hold with a straight body line!"
    },
}

# Default tips for exercises not in the map
DEFAULT_TIPS = {
    "low_rom": "Try to use a fuller range of motion for better results.",
    "poor_stability": "Focus on controlled movements to improve stability.",
    "good_form": "Good exercise form detected!"
}


def aggregate_joint_importance(shap_values, feature_names):
    """
    Aggregate SHAP values from individual features (x_0, y_0, z_0, v_0, ...)
    into per-joint importance scores.
    
    Returns: dict {joint_name: importance_score}
    """
    joint_scores = {}
    
    for i in range(33):
        # Sum absolute SHAP values for all 4 features of this joint
        joint_shap = 0.0
        for prefix in ["x", "y", "z", "v"]:
            # Try both naming conventions
            for col_name in [f"{prefix}_{i}", f"{prefix}{i}"]:
                if col_name in feature_names:
                    idx = list(feature_names).index(col_name)
                    if idx < len(shap_values):
                        joint_shap += abs(float(shap_values[idx]))
                    break
        
        if joint_shap > 0:
            joint_scores[LANDMARK_NAMES[i]] = round(joint_shap, 4)
    
    return joint_scores


def get_top_joints(joint_importance, exercise=None, top_n=5):
    """Get top N most important joints, prioritizing exercise-relevant ones."""
    if not joint_importance:
        return []
    
    sorted_joints = sorted(joint_importance.items(), key=lambda x: x[1], reverse=True)
    return sorted_joints[:top_n]


def generate_form_explanation(exercise, form, avg_rom, avg_stability, avg_tempo,
                               reps_correct, reps_wrong, reps_total,
                               joint_importance=None, confidence=0.0):
    """
    Generate structured, natural language explanation of the AI's form assessment.
    
    Returns: dict with 'insights' list and 'summary' string
    """
    insights = []
    exercise_lower = exercise.lower() if exercise else "unknown"
    tips = EXERCISE_FORM_TIPS.get(exercise_lower, DEFAULT_TIPS)
    
    # ──── 1. Overall Form Verdict ────
    if form == "correct":
        insights.append({
            "type": "success",
            "icon": "check_circle",
            "title": "Form Assessment: Correct",
            "message": tips.get("good_form", DEFAULT_TIPS["good_form"]),
            "severity": "good"
        })
    elif form == "wrong":
        insights.append({
            "type": "warning",
            "icon": "error",
            "title": "Form Assessment: Needs Improvement",
            "message": "The AI detected form issues in your exercise. See details below.",
            "severity": "critical"
        })
    else:
        insights.append({
            "type": "info",
            "icon": "help",
            "title": "Form Assessment: Undetermined",
            "message": "Not enough data to assess form accurately.",
            "severity": "info"
        })
    
    # ──── 2. Range of Motion Analysis ────
    if avg_rom is not None and avg_rom > 0:
        if avg_rom >= 80:
            insights.append({
                "type": "metric",
                "icon": "straighten",
                "title": f"Range of Motion: {avg_rom:.0f}%",
                "message": "Excellent range of motion! You're using the full movement path.",
                "severity": "good"
            })
        elif avg_rom >= 60:
            insights.append({
                "type": "metric",
                "icon": "straighten",
                "title": f"Range of Motion: {avg_rom:.0f}%",
                "message": "Decent range of motion, but there's room to go deeper for better muscle activation.",
                "severity": "warning"
            })
        elif avg_rom >= 45:
            insights.append({
                "type": "metric",
                "icon": "straighten",
                "title": f"Range of Motion: {avg_rom:.0f}%",
                "message": f"Limited range of motion detected. {tips.get('low_rom', DEFAULT_TIPS['low_rom'])}",
                "severity": "warning"
            })
        else:
            insights.append({
                "type": "metric",
                "icon": "straighten",
                "title": f"Range of Motion: {avg_rom:.0f}% ⚠️",
                "message": f"Very limited range of motion. {tips.get('low_rom', DEFAULT_TIPS['low_rom'])}",
                "severity": "critical"
            })
    
    # ──── 3. Stability Analysis ────
    if avg_stability is not None and avg_stability > 0:
        if avg_stability >= 80:
            insights.append({
                "type": "metric",
                "icon": "balance",
                "title": f"Stability Score: {avg_stability:.0f}/100",
                "message": "Your body is very stable during the exercise — great core engagement!",
                "severity": "good"
            })
        elif avg_stability >= 60:
            insights.append({
                "type": "metric",
                "icon": "balance",
                "title": f"Stability Score: {avg_stability:.0f}/100",
                "message": "Some body sway detected. Try bracing your core harder.",
                "severity": "warning"
            })
        else:
            insights.append({
                "type": "metric",
                "icon": "balance",
                "title": f"Stability Score: {avg_stability:.0f}/100",
                "message": f"Significant body instability detected. {tips.get('poor_stability', DEFAULT_TIPS['poor_stability'])}",
                "severity": "critical"
            })
    
    # ──── 4. Tempo Analysis ────
    if avg_tempo is not None and avg_tempo > 0:
        if 1.5 <= avg_tempo <= 4.0:
            insights.append({
                "type": "metric",
                "icon": "speed",
                "title": f"Tempo: {avg_tempo:.1f}s per rep",
                "message": "Good controlled tempo — the AI detected a consistent pace.",
                "severity": "good"
            })
        elif avg_tempo < 1.5:
            insights.append({
                "type": "metric",
                "icon": "speed",
                "title": f"Tempo: {avg_tempo:.1f}s per rep",
                "message": "You're moving very fast. Slow down for better muscle engagement and form control.",
                "severity": "warning"
            })
        else:
            insights.append({
                "type": "metric",
                "icon": "speed",
                "title": f"Tempo: {avg_tempo:.1f}s per rep",
                "message": "Slow tempo detected. While time under tension is good, ensure you're not struggling with the weight.",
                "severity": "info"
            })
    
    # ──── 5. Rep Quality Breakdown ────
    if reps_total and reps_total > 0:
        correct_pct = (reps_correct / reps_total * 100) if reps_total > 0 else 0
        if correct_pct >= 90:
            insights.append({
                "type": "metric",
                "icon": "emoji_events",
                "title": f"Rep Quality: {reps_correct}/{reps_total} correct ({correct_pct:.0f}%)",
                "message": "Nearly perfect execution across all reps!",
                "severity": "good"
            })
        elif correct_pct >= 60:
            insights.append({
                "type": "metric",
                "icon": "trending_up",
                "title": f"Rep Quality: {reps_correct}/{reps_total} correct ({correct_pct:.0f}%)",
                "message": f"{reps_wrong} reps had form issues. Focus on maintaining form even as you fatigue.",
                "severity": "warning"
            })
        else:
            insights.append({
                "type": "metric",
                "icon": "trending_down",
                "title": f"Rep Quality: {reps_correct}/{reps_total} correct ({correct_pct:.0f}%)",
                "message": f"Most reps ({reps_wrong}) had form issues. Consider reducing weight to focus on proper technique.",
                "severity": "critical"
            })
    
    # ──── 6. AI Focus Explanation (SHAP-based) ────
    if joint_importance:
        top_joints = get_top_joints(joint_importance, exercise, top_n=3)
        if top_joints:
            joint_names = [j[0] for j in top_joints]
            joints_str = ", ".join(joint_names[:2])
            if len(joint_names) > 2:
                joints_str += f", and {joint_names[2]}"
            
            insights.append({
                "type": "xai",
                "icon": "psychology",
                "title": "AI Focus Points",
                "message": f"The AI primarily analyzed your {joints_str} to make its assessment.",
                "severity": "info",
                "details": {name: float(score) for name, score in top_joints}
            })
    
    # ──── 7. Confidence Insight ────
    if confidence > 0:
        if confidence >= 85:
            conf_msg = "The AI is highly confident in this assessment."
        elif confidence >= 70:
            conf_msg = "The AI has moderate confidence. Results should be reliable."
        else:
            conf_msg = "The AI has lower confidence — ensure full body visibility for better results."
        
        insights.append({
            "type": "confidence",
            "icon": "verified",
            "title": f"AI Confidence: {confidence:.0f}%",
            "message": conf_msg,
            "severity": "good" if confidence >= 70 else "warning"
        })
    
    # ──── Build Summary ────
    summary = _build_summary(exercise_lower, form, avg_rom, avg_stability,
                              reps_correct, reps_wrong, reps_total, confidence)
    
    return {
        "insights": insights,
        "summary": summary,
        "exercise": exercise,
        "form": form
    }


def _build_summary(exercise, form, avg_rom, avg_stability,
                    reps_correct, reps_wrong, reps_total, confidence):
    """Build a concise 1-2 sentence AI summary."""
    exercise_display = exercise.replace("_", " ").title()
    
    if form == "correct":
        base = f"Your {exercise_display} form looks good"
        details = []
        if avg_rom and avg_rom >= 70:
            details.append(f"strong ROM ({avg_rom:.0f}%)")
        if avg_stability and avg_stability >= 70:
            details.append(f"good stability ({avg_stability:.0f}%)")
        if reps_total and reps_total > 0 and reps_correct == reps_total:
            details.append(f"all {reps_total} reps clean")
        
        if details:
            return f"{base} — {', '.join(details)}. Keep it up!"
        return f"{base}. Keep up the good work!"
    
    elif form == "wrong":
        issues = []
        if avg_rom and avg_rom < 60:
            issues.append(f"limited range of motion ({avg_rom:.0f}%)")
        if avg_stability and avg_stability < 60:
            issues.append(f"body instability ({avg_stability:.0f}%)")
        if reps_wrong and reps_wrong > 0:
            issues.append(f"{reps_wrong} reps with form issues")
        
        if issues:
            return f"Your {exercise_display} needs work: {', '.join(issues)}. Focus on technique over weight."
        return f"Your {exercise_display} form needs improvement. Watch your technique carefully."
    
    return f"Completed {exercise_display} analysis."


def generate_per_rep_data(rep_roms, rep_durations, reps_correct, reps_wrong, reps_total):
    """
    Generate per-rep quality timeline data.
    Combines ROM and duration into a per-rep breakdown.
    """
    reps_data = []
    num_reps = max(len(rep_roms), len(rep_durations), reps_total or 0)
    
    if num_reps == 0:
        return reps_data
    
    for i in range(num_reps):
        rep = {
            "rep_number": i + 1,
            "rom_pct": round(rep_roms[i], 1) if i < len(rep_roms) else None,
            "duration": round(rep_durations[i], 2) if i < len(rep_durations) else None,
        }
        
        # Determine rep quality based on ROM
        if rep["rom_pct"] is not None:
            if rep["rom_pct"] >= 70:
                rep["quality"] = "good"
            elif rep["rom_pct"] >= 45:
                rep["quality"] = "fair"
            else:
                rep["quality"] = "poor"
        else:
            rep["quality"] = "unknown"
        
        reps_data.append(rep)
    
    return reps_data
