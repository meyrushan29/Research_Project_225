from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
import os
import uuid
import random
from sqlalchemy.orm import Session
from core.models import User, FitnessAnalysis, ExerciseMetadata, FitnessNotification, MuscleRadarHistory
from core.deps import get_current_user, get_db

router = APIRouter(
    prefix="/predict/fitness",
    tags=["Fitness"]
)

@router.post("/video")
def predict_fitness_video(
    video: UploadFile = File(...),
    enable_heatmap: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        try:
            from fitness.api_handler import get_processor
        except Exception as imp_err:
            raise HTTPException(
                status_code=503,
                detail=f"Fitness processor unavailable: {imp_err}"
            )

        os.makedirs("temp", exist_ok=True)
        temp_filename = f"temp/{uuid.uuid4()}_{video.filename}"
        
        with open(temp_filename, "wb") as f:
            while True:
                chunk = video.file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                f.write(chunk)
            
        # Use absolute path for output directory to ensure consistency
        output_dir = os.path.join(os.getcwd(), "img", "fitness_processed")
        os.makedirs(output_dir, exist_ok=True)
        
        processor = get_processor()
        result = processor.process_video(temp_filename, output_dir=output_dir, enable_heatmap=enable_heatmap)
        
        if "error" in result:
             if "No human detected" in result["error"]:
                 raise HTTPException(status_code=400, detail=result["error"])
             raise HTTPException(status_code=500, detail=result["error"])
        
        result["video_url"] = f"/fitness_videos/{result['processed_video_filename']}"
        
        # ── SAFETY: Ensure exercise field is clean (no _correct / _wrong suffix) ──
        raw_exercise = result.get("exercise", "unknown")
        if raw_exercise.endswith("_correct"):
            raw_exercise = raw_exercise[:-8]
        elif raw_exercise.endswith("_wrong"):
            raw_exercise = raw_exercise[:-6]
        result["exercise"] = raw_exercise
        print(f"✅ API RESPONSE -> exercise='{raw_exercise}', form='{result.get('form', 'unknown')}', confidence={result.get('confidence', 0):.1f}%")
        
        video_url_normal = None
        video_url_heatmap = None

        if "video_filename_normal" in result:
             video_url_normal = f"/fitness_videos/{result['video_filename_normal']}"
             result["video_url_normal"] = video_url_normal
        if "video_filename_heatmap" in result:
             video_url_heatmap = f"/fitness_videos/{result['video_filename_heatmap']}"
             result["video_url_heatmap"] = video_url_heatmap
        
        # ── NEW: Inaccuracy Warning for New Users (< 20 videos) ──
        try:
            user_session_count = db.query(FitnessAnalysis).filter(FitnessAnalysis.user_id == current_user.id).count()
            if user_session_count < 20:
                result["accuracy_warning"] = "The system may not accurately identify correct form until you have uploaded at least 20 workout videos. " \
                                           f"Your current workout count: {user_session_count}/20."
        except Exception as e:
            print(f"Warning: Failed to fetch user session count: {e}")

        # --- RECOMMENDATION LOGIC START ---
        try:
            current_exercise_name = result.get("exercise", "").lower().replace("_", " ")
            current_metadata = db.query(ExerciseMetadata).filter(ExerciseMetadata.name == current_exercise_name).first()
            current_body_part = current_metadata.body_part if current_metadata else "General"
            
            # Get last session
            last_session = db.query(FitnessAnalysis).filter(
                FitnessAnalysis.user_id == current_user.id
            ).order_by(FitnessAnalysis.timestamp.desc()).first()
            
            recommendation_msg = ""
            target_part = None
            
            all_parts = ["Chest", "Back", "Legs", "Arms", "Shoulders", "Core"]
            
            if last_session:
                last_exercise_name = last_session.exercise.lower().replace("_", " ") if last_session.exercise else "unknown"
                last_metadata = db.query(ExerciseMetadata).filter(ExerciseMetadata.name == last_exercise_name).first()
                last_body_part = last_metadata.body_part if last_metadata else "General"
                
                if last_body_part == current_body_part and current_body_part != "General":
                    # User is using same body part sequentially
                    available = [p for p in all_parts if p != current_body_part]
                    target_part = random.choice(available) if available else "Core"
                    recommendation_msg = f"Last time you also worked on {last_body_part} ({last_exercise_name}). " \
                                         f"To balance your fitness, try focusing on {target_part} next."
                else:
                    # Good balance or unknown
                    available = [p for p in all_parts if p != current_body_part] # Simply suggest something different for next time
                    if last_body_part != "General":
                         available = [p for p in available if p != last_body_part]
                    
                    target_part = random.choice(available) if available else "Core"
                    
                    if last_session:
                         recommendation_msg = f"Great work! You switched from {last_body_part} to {current_body_part}. " \
                                              f"For your next workout, consider targeting {target_part}."
                    else:
                         recommendation_msg = f"Good workout targeting {current_body_part}. For next time, try {target_part}."

            else:
                # First session ever
                available = [p for p in all_parts if p != current_body_part]
                target_part = random.choice(available) if available else "Core"
                recommendation_msg = f"Welcome! You are starting with {current_body_part}. " \
                                     f"Next time, try an exercise for {target_part} to build a full routine."

            # Find specific exercises for the target part
            if target_part:
                suggested_ex_objs = db.query(ExerciseMetadata).filter(ExerciseMetadata.body_part == target_part).limit(3).all()
                suggested_names = [e.name.title() for e in suggested_ex_objs]
                if suggested_names:
                    recommendation_msg += f" Try: {', '.join(suggested_names)}."
            
            result["recommendation"] = recommendation_msg
            
            # Add to details for persistence
            existing_details = result.get("advanced_metrics", {})
            if not isinstance(existing_details, dict):
                existing_details = {}
            existing_details["recommendation"] = recommendation_msg
            result["advanced_metrics"] = existing_details
            
        except Exception as rec_err:
            print(f"Recommendation generation failed: {rec_err}")
            # Non-critical, continue
        # --- RECOMMENDATION LOGIC END ---
        
        # Save to History (include XAI data in details)
        try:
            details_to_save = result.get("advanced_metrics", {})
            if not isinstance(details_to_save, dict):
                details_to_save = {}
            
            # Add XAI data to details
            xai_data = result.get("xai_explanation", {})
            if xai_data:
                details_to_save["xai_explanation"] = xai_data
            joint_imp = result.get("joint_importance", {})
            if joint_imp:
                details_to_save["joint_importance"] = joint_imp
            per_rep = result.get("per_rep_timeline", [])
            if per_rep:
                details_to_save["per_rep_timeline"] = per_rep
            
            analysis_entry = FitnessAnalysis(
                user_id=current_user.id,
                exercise=result.get("exercise", "unknown"),
                form=result.get("form", "unknown"),
                confidence=float(result.get("confidence", 0.0)),
                reps_total=int(result.get("reps", 0)),
                reps_correct=int(result.get("reps_correct", 0)),
                reps_wrong=int(result.get("reps_wrong", 0)),
                hold_time=float(result.get("hold_time", 0.0)),
                video_path_input=None, # We don't save input video to save space
                video_path_normal=video_url_normal,
                video_path_heatmap=video_url_heatmap,
                details=details_to_save
            )
            db.add(analysis_entry)
            db.commit()
            db.refresh(analysis_entry)
            result["history_id"] = analysis_entry.id

            # ── 30-session cycle: save radar snapshot when a cycle completes ──
            try:
                total_count = (
                    db.query(FitnessAnalysis)
                    .filter(FitnessAnalysis.user_id == current_user.id)
                    .count()
                )
                cycle_size = 30
                if total_count > 0 and total_count % cycle_size == 0:
                    completed_cycle = total_count // cycle_size   # 1-based
                    session_start   = (completed_cycle - 1) * cycle_size + 1
                    session_end     = completed_cycle * cycle_size

                    # Fetch the 30 sessions that just completed
                    cycle_sessions = (
                        db.query(FitnessAnalysis)
                        .filter(FitnessAnalysis.user_id == current_user.id)
                        .order_by(FitnessAnalysis.timestamp.asc())
                        .offset((completed_cycle - 1) * cycle_size)
                        .limit(cycle_size)
                        .all()
                    )

                    radar_snapshot = _compute_radar(cycle_sessions)

                    radar_entry = MuscleRadarHistory(
                        user_id       = current_user.id,
                        cycle_number  = completed_cycle,
                        session_start = session_start,
                        session_end   = session_end,
                        radar_data    = radar_snapshot,
                        total_sessions = cycle_size,
                    )
                    db.add(radar_entry)
                    db.commit()
                    print(f"[MuscleRadar] Cycle {completed_cycle} snapshot saved "
                          f"(sessions {session_start}–{session_end}): {radar_snapshot}")
            except Exception as radar_err:
                print(f"[MuscleRadar] Failed to save cycle snapshot: {radar_err}")
                # Non-critical — don't fail the request

        except Exception as db_err:
            print(f"Warning: Failed to save history: {db_err}")
            # Don't fail the request, just log it

        return result
        
    except Exception as e:
        print(f"FITNESS PREDICT ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

@router.get("/history")
def get_fitness_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get past fitness analysis sessions for the current user"""
    history = db.query(FitnessAnalysis).filter(
        FitnessAnalysis.user_id == current_user.id
    ).order_by(FitnessAnalysis.timestamp.desc()).limit(limit).all()
    return history

@router.get("/recommendation")
def get_fitness_recommendation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered workout recommendation based on previous activity.
    Logic: Checks last worked body part -> Suggests complementary body part.
    """
    try:
        # 1. Get last session
        last_session = db.query(FitnessAnalysis).filter(
            FitnessAnalysis.user_id == current_user.id
        ).order_by(FitnessAnalysis.timestamp.desc()).first()
        
        all_parts = ["Chest", "Back", "Legs", "Arms", "Shoulders", "Core"]
        
        if not last_session:
            # New User
            return {
                "message": "Welcome to your AI Fitness Journey! To get started, we recommend a foundational compound exercise.",
                "last_worked": "None",
                "target_part": "Full Body",
                "suggested_exercises": ["Squat", "Push-up", "Plank"]
            }
            
        # 2. Identify last body part
        last_exercise_name = last_session.exercise.lower().replace("_", " ") if last_session.exercise else "unknown"
        # Find in metadata
        last_metadata = db.query(ExerciseMetadata).filter(ExerciseMetadata.name == last_exercise_name).first()
        last_body_part = last_metadata.body_part if last_metadata else "General"
        
        # 3. Determine next target
        available = [p for p in all_parts if p != last_body_part]
        # Prefer major groups if last was small, etc. Simple random for now.
        target_part = random.choice(available) if available else "Core"
        
        # 4. Generate Message
        message = f"Your last workout focused on {last_body_part} ({last_exercise_name.capitalize()}). " \
                  f"To maintain balance, let's target your {target_part} next!"
                  
        # 5. Suggest Exercises
        suggested_ex_objs = db.query(ExerciseMetadata).filter(ExerciseMetadata.body_part == target_part).limit(4).all()
        suggested_names = [e.name.replace("_", " ").title() for e in suggested_ex_objs]
        if not suggested_names:
            suggested_names = ["Squat", "Plank"] # Fallback
        
        return {
            "message": message,
            "last_worked": last_body_part,
            "target_part": target_part,
            "suggested_exercises": suggested_names
        }

    except Exception as e:
        print(f"Error generating recommendation: {e}")
        # Return fallback instead of error to not break frontend
        return {
            "message": "Start with a balanced workout today!",
            "last_worked": "Unknown",
            "target_part": "Full Body",
            "suggested_exercises": ["Squat", "Push-up"]
        }

@router.post("/analyze")
def analyze_fitness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyzes the last 3 exercises the user did.
    Recommends the next body part based on categories.
    """
    try:
        # Get last 3 fitness sessions
        last_sessions = db.query(FitnessAnalysis).filter(
            FitnessAnalysis.user_id == current_user.id
        ).order_by(FitnessAnalysis.timestamp.desc()).limit(3).all()

        if not last_sessions:
            msg = "No recent exercises found. Start your first workout today!"
            notif = FitnessNotification(
                user_id=current_user.id,
                exercises_analyzed=[],
                targeted_parts=[],
                categories=[],
                message=msg
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)
            return notif

        ex_names = []
        for s in last_sessions:
            raw_ex = s.exercise.lower().replace("_", " ") if s.exercise else ""
            if raw_ex and raw_ex != "unknown" and raw_ex != "initializing":
                ex_names.append(raw_ex)
        
        if not ex_names:
            msg = "Recent exercises were unrecognizable. Please ensure full body visibility when working out."
            notif = FitnessNotification(
                user_id=current_user.id,
                exercises_analyzed=[],
                targeted_parts=[],
                categories=[],
                message=msg
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)
            return notif

        # unique exercises to avoid double counting same exercise twice
        unique_exs = list(set(ex_names))
        
        # get metadata
        metas = db.query(ExerciseMetadata).filter(ExerciseMetadata.name.in_(unique_exs)).all()
        
        targeted_parts = {}
        target_categories = {}
        
        for meta in metas:
            if meta.body_part:
                targeted_parts[meta.body_part] = targeted_parts.get(meta.body_part, 0) + 1
            if meta.target_category:
                target_categories[meta.target_category] = target_categories.get(meta.target_category, 0) + 1
        
        parts_list = list(targeted_parts.keys())
        cat_list = list(target_categories.keys())

        # Logic for message
        ex_str = ", ".join([e.title() for e in unique_exs])
        cat_str = " and ".join(cat_list) if len(cat_list) <= 2 else ", ".join(cat_list[:-1]) + ", and " + cat_list[-1]
        
        msg = f"In your recent sessions, you performed: {ex_str}. "
        if cat_str:
            msg += f"These exercises primarily targeted your {cat_str}. "
        
        # Recommendations
        all_cats = ["Upper Body Push", "Upper Body Pull", "Lower Body", "Core"]
        available_cats = [c for c in all_cats if c not in cat_list]
        
        if available_cats:
            target_next = available_cats[0]
            # Get some suggestions for target_next
            suggestions = db.query(ExerciseMetadata).filter(ExerciseMetadata.target_category == target_next).limit(3).all()
            sugg_names = [s.name.title() for s in suggestions]
            sugg_str = ", ".join(sugg_names)
            
            msg += f"For a balanced fitness routine, we recommend focusing on {target_next} next."
            if sugg_names:
                msg += f"\n\nSuggested exercises to try: {sugg_str}."
        else:
            msg += "Great job mixing up your routine! You have hit all major body regions recently."

        notif = FitnessNotification(
            user_id=current_user.id,
            exercises_analyzed=ex_names,
            targeted_parts=parts_list,
            categories=cat_list,
            message=msg
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        
        return notif

    except Exception as e:
        print(f"Error generating analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze fitness history")

@router.get("/notifications")
def get_fitness_notifications(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the history of fitness analyses for the current user.
    """
    history = db.query(FitnessNotification).filter(
        FitnessNotification.user_id == current_user.id
    ).order_by(FitnessNotification.timestamp.desc()).limit(limit).all()
    return history

@router.get("/progress")
def get_fitness_progress(
    exercise: str = None,
    limit: int = 10,
    cycle_number: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get fitness progress data for XAI trend tracking.
    Returns ROM, stability, tempo trends across sessions.
    If cycle_number is provided, fetches the exact 30 sessions for that cycle.
    """
    try:
        query = db.query(FitnessAnalysis).filter(
            FitnessAnalysis.user_id == current_user.id
        )
        
        if exercise:
            query = query.filter(FitnessAnalysis.exercise == exercise.lower())
        
        # If cycle_number is specified, fetch the exact 30 sessions for that cycle
        if cycle_number is not None and cycle_number > 0:
            cycle_size = 30
            offset = (cycle_number - 1) * cycle_size
            # Order ascending first to get the correct block of 30 for that cycle
            cycle_sessions = query.order_by(FitnessAnalysis.timestamp.asc()).offset(offset).limit(cycle_size).all()
            # Then reverse them so the newest in that cycle is first, matching the normal default behavior
            sessions = list(reversed(cycle_sessions))
        else:
            sessions = query.order_by(FitnessAnalysis.timestamp.desc()).limit(limit).all()
        
        if not sessions:
            return {
                "message": "No workout sessions found. Start exercising to track your progress!",
                "sessions": [],
                "trends": {},
                "ai_summary": "Upload your first workout video to begin tracking your fitness journey."
            }
        
        # Extract metrics from each session
        progress_data = []
        rom_values = []
        stability_values = []
        tempo_values = []
        form_results = []
        
        for session in reversed(sessions):  # Chronological order
            details = session.details or {}
            
            entry = {
                "id": session.id,
                "exercise": session.exercise,
                "form": session.form,
                "confidence": session.confidence,
                "reps_total": session.reps_total,
                "reps_correct": session.reps_correct,
                "reps_wrong": session.reps_wrong,
                "timestamp": session.timestamp.isoformat() if session.timestamp else None,
                "avg_rom": details.get("avg_rom"),
                "avg_stability": details.get("avg_stability"),
                "avg_tempo": details.get("avg_tempo"),
            }
            progress_data.append(entry)
            
            if details.get("avg_rom") is not None:
                rom_values.append(float(details["avg_rom"]))
            if details.get("avg_stability") is not None:
                stability_values.append(float(details["avg_stability"]))
            if details.get("avg_tempo") is not None:
                tempo_values.append(float(details["avg_tempo"]))
            form_results.append(session.form)
        
        # Calculate trends
        def calc_trend(values):
            if len(values) < 2:
                return "neutral"
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            avg_first = sum(first_half) / len(first_half) if first_half else 0
            avg_second = sum(second_half) / len(second_half) if second_half else 0
            diff = avg_second - avg_first
            if diff > 3:
                return "improving"
            elif diff < -3:
                return "declining"
            return "stable"
        
        trends = {
            "rom": calc_trend(rom_values),
            "stability": calc_trend(stability_values),
            "tempo": calc_trend(tempo_values),
        }
        
        # Form accuracy trend
        correct_count = form_results.count("correct")
        total = len(form_results)
        form_accuracy = (correct_count / total * 100) if total > 0 else 0
        trends["form_accuracy"] = round(form_accuracy, 1)
        
        # Generate AI summary
        exercise_display = exercise.replace("_", " ").title() if exercise else "overall fitness"
        summary_parts = []
        
        if trends["rom"] == "improving":
            summary_parts.append(f"Your range of motion for {exercise_display} is improving")
        elif trends["rom"] == "declining":
            summary_parts.append(f"Your range of motion has decreased — focus on full depth")
        
        if trends["stability"] == "improving":
            summary_parts.append("your stability is getting better")
        elif trends["stability"] == "declining":
            summary_parts.append("watch your stability — core engagement may be dropping")
        
        if form_accuracy >= 80:
            summary_parts.append(f"form accuracy is strong at {form_accuracy:.0f}%")
        elif form_accuracy < 50:
            summary_parts.append(f"form accuracy needs work ({form_accuracy:.0f}%) — consider reducing weight")
        
        if summary_parts:
            ai_summary = ". ".join(s.capitalize() if i == 0 else s for i, s in enumerate(summary_parts)) + "."
        else:
            ai_summary = f"Keep training! More data will unlock detailed progress insights for {exercise_display}."
        
        return {
            "sessions": progress_data,
            "trends": trends,
            "ai_summary": ai_summary,
            "total_sessions": total,
            "metrics_summary": {
                "avg_rom": round(sum(rom_values) / len(rom_values), 1) if rom_values else None,
                "avg_stability": round(sum(stability_values) / len(stability_values), 1) if stability_values else None,
                "avg_tempo": round(sum(tempo_values) / len(tempo_values), 2) if tempo_values else None,
            }
        }
    except Exception as e:
        print(f"Error generating progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate progress data: {e}")


# ─── Muscle Group Radar ─────────────────────────────────────────────────────
# Exercise → Muscle Group mapping (6 groups based on the 20 supported exercises)

_MUSCLE_GROUPS = ["Arms", "Chest", "Back", "Shoulders", "Core", "Legs"]

_EXERCISE_MUSCLE_GROUP: dict[str, str] = {
    # Arms
    "barbell biceps curl": "Arms",
    "hammer curl":         "Arms",
    "tricep dips":         "Arms",
    "tricep pushdown":     "Arms",
    # Chest
    "bench press":         "Chest",
    "incline bench press": "Chest",
    "push up":             "Chest",
    # Back
    "deadlift":            "Back",
    "lat pulldown":        "Back",
    "pull up":             "Back",
    "t bar row":           "Back",
    # Shoulders
    "lateral raise":       "Shoulders",
    "shoulder press":      "Shoulders",
    # Core
    "leg raises":          "Core",
    "plank":               "Core",
    "russian twist":       "Core",
    # Legs
    "hip thrust":          "Legs",
    "leg extension":       "Legs",
    "romanian deadlift":   "Legs",
    "squat":               "Legs",
}


def _normalise_exercise(raw: str) -> str:
    """Lowercase + replace underscores → space, strip whitespace."""
    return (raw or "").strip().lower().replace("_", " ")


def _compute_radar(sessions: list) -> dict[str, float]:
    """
    Given a list of FitnessAnalysis ORM objects, return a dict of
    muscle group → score (0–100), where score is proportional to how
    many sessions targeted that group (each session contributes 1 count).
    """
    counts: dict[str, int] = {g: 0 for g in _MUSCLE_GROUPS}
    for s in sessions:
        ex = _normalise_exercise(s.exercise)
        group = _EXERCISE_MUSCLE_GROUP.get(ex)
        if group:
            counts[group] += 1

    total = sum(counts.values()) or 1   # avoid div-by-zero
    return {
        g: round((counts[g] / total) * 100, 1)
        for g in _MUSCLE_GROUPS
    }


@router.get("/body-part-radar")
def get_body_part_radar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the Muscle Focus Radar for the user's CURRENT 30-session cycle.

    - Each 30 sessions = 1 cycle.  After 30 sessions the radar resets to 0.
    - Returns radar scores (0-100), the current session count in this cycle,
      which cycle we are in, and how many sessions remain until reset.
    """
    try:
        # ── Total sessions ever (to determine cycle position) ──────────────
        total_count: int = (
            db.query(FitnessAnalysis)
            .filter(FitnessAnalysis.user_id == current_user.id)
            .count()
        )

        cycle_size    = 30
        cycle_number  = (total_count // cycle_size) + 1          # 1-based
        sessions_done = total_count % cycle_size                  # 0 → 29

        # ── Fetch only the current-cycle sessions ──────────────────────────
        # Skip the first (cycle_number-1)*30 sessions (they belong to past cycles)
        sessions_to_skip = (cycle_number - 1) * cycle_size
        current_sessions = (
            db.query(FitnessAnalysis)
            .filter(FitnessAnalysis.user_id == current_user.id)
            .order_by(FitnessAnalysis.timestamp.asc())
            .offset(sessions_to_skip)
            .limit(cycle_size)
            .all()
        )

        radar = _compute_radar(current_sessions)

        return {
            **radar,
            "current_session":    sessions_done,          # how many done so far (0–29)
            "cycle_size":         cycle_size,
            "cycle_number":       cycle_number,
            "sessions_remaining": cycle_size - sessions_done,
            "total_sessions_ever": total_count,
        }

    except Exception as e:
        print(f"Error generating body-part radar: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate radar data: {e}"
        )


@router.get("/muscle-radar-history")
def get_muscle_radar_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all completed 30-session Muscle Radar snapshots for the user,
    oldest first. Each entry contains the cycle number, completion date,
    and the radar scores.
    """
    try:
        history = (
            db.query(MuscleRadarHistory)
            .filter(MuscleRadarHistory.user_id == current_user.id)
            .order_by(MuscleRadarHistory.cycle_number.asc())
            .all()
        )

        return [
            {
                "id":            h.id,
                "cycle_number":  h.cycle_number,
                "completed_at":  h.completed_at.isoformat() if h.completed_at else None,
                "session_start": h.session_start,
                "session_end":   h.session_end,
                "radar_data":    h.radar_data,
                "total_sessions": h.total_sessions,
            }
            for h in history
        ]

    except Exception as e:
        print(f"Error fetching radar history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch radar history: {e}"
        )


_BODY_PART_LABELS = ["Arms", "Shoulders", "Chest", "Back", "Core", "Legs"]


@router.get("/body-part-radar")
def get_body_part_radar(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns per-body-part SHAP importance scores aggregated across all the
    user's past fitness sessions. Used to render the Radar / Spider chart.

    Strategy:
    - Each session → look up exercise body_part (Arms / Legs / Chest …)
    - If SHAP joint_importance exists: use its total as the session weight
    - If not: flat weight of 1.0
    - Accumulate weighted totals per body part, normalise to 0-100

    This avoids the "all Core" bug caused by hips always having high SHAP
    values in every exercise as the model uses them as a reference anchor.
    """
    try:
        sessions = (
            db.query(FitnessAnalysis)
            .filter(FitnessAnalysis.user_id == current_user.id)
            .order_by(FitnessAnalysis.timestamp.desc())
            .limit(limit)
            .all()
        )

        body_part_scores: dict[str, float] = {bp: 0.0 for bp in _BODY_PART_LABELS}
        body_part_counts: dict[str, int]   = {bp: 0   for bp in _BODY_PART_LABELS}
        has_shap_data = False

        for session in sessions:
            # ── Normalise exercise name (handles both "squat" and "barbell_biceps_curl")
            raw_ex   = (session.exercise or "").strip().lower().replace("_", " ")
            if not raw_ex or raw_ex in ("unknown", "initializing"):
                continue

            # ── Look up body part from metadata
            meta = db.query(ExerciseMetadata).filter(
                ExerciseMetadata.name == raw_ex
            ).first()

            if meta is None:
                # Try with underscores (legacy storage)
                raw_ex_under = raw_ex.replace(" ", "_")
                meta = db.query(ExerciseMetadata).filter(
                    ExerciseMetadata.name == raw_ex_under
                ).first()

            body_part = meta.body_part if meta else None
            if not body_part or body_part not in body_part_scores:
                # Unknown exercise – skip rather than corrupt totals
                continue

            # ── Compute session weight from SHAP scores
            details = session.details or {}
            joint_importance: dict = details.get("joint_importance", {})

            if joint_importance:
                has_shap_data = True
                # Sum all joint SHAP scores → the overall "AI importance" for this session
                shap_total = sum(abs(float(v)) for v in joint_importance.values())
                weight = max(shap_total, 0.1)   # guard against zero/negative
            else:
                # No SHAP yet → flat contribution so older sessions still show
                weight = 1.0

            body_part_scores[body_part] += weight
            body_part_counts[body_part] += 1

        # ── Normalise to 0–100
        max_score = max(body_part_scores.values()) if any(
            v > 0 for v in body_part_scores.values()
        ) else 1.0

        normalised = {
            bp: round((score / max_score) * 100, 1)
            for bp, score in body_part_scores.items()
        }

        return {
            **normalised,
            "session_count": len(sessions),
            "has_shap_data": has_shap_data,
        }

    except Exception as e:
        print(f"Error generating body-part radar: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate radar data: {e}"
        )

