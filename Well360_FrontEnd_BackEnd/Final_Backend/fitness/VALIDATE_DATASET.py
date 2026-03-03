"""
VALIDATE_DATASET.py
===================
Analyzes and cleans the fitness video dataset.

For each video it checks:
  1. Can MediaPipe detect a full-body pose?
  2. Are key landmark visibility scores acceptable?
  3. Does the video have enough usable frames?
  4. Is the pose stable (not shaky / obstructed)?

Videos that fail are moved to  dataset/_rejected/<exercise>/<label>/
A full CSV report is written to  dataset/VALIDATION_REPORT.csv

Usage:
    cd Final_Backend/fitness
    python VALIDATE_DATASET.py           # dry-run (just reports)
    python VALIDATE_DATASET.py --delete  # actually moves bad videos
"""

import cv2
import os
import sys
import csv
import shutil
import argparse
from pathlib import Path
from collections import defaultdict

# Windows: force UTF-8 so emoji characters don't crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ── MediaPipe ──────────────────────────────────────────────────────────────
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    print("OK  MediaPipe loaded")
except Exception as e:
    print(f"ERROR MediaPipe unavailable: {e}")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────────────
DATASET_DIR   = Path("dataset")
REJECTED_DIR  = DATASET_DIR / "_rejected"
REPORT_CSV    = DATASET_DIR / "VALIDATION_REPORT.csv"

# Sample this many frames evenly from each video (fast check)
SAMPLE_FRAMES = 20

# Thresholds  — tweak these if too strict / too lenient
MIN_POSE_DETECTION_RATE = 0.40   # At least 40% of sampled frames must have a pose
MIN_KEY_VISIBILITY      = 0.50   # Key landmarks must be ≥50% visible on average
MIN_USABLE_FRAMES       = 8      # Video must yield at least 8 usable frames
MIN_VIDEO_SECONDS       = 1.0    # Video must be at least 1 second long

# For whole-body exercises we need these landmarks clearly visible
# (indices from MediaPipe Pose — 33 landmarks)
UPPER_BODY_LANDMARKS = [11, 12, 13, 14, 15, 16]   # shoulders, elbows, wrists
LOWER_BODY_LANDMARKS = [23, 24, 25, 26, 27, 28]   # hips, knees, ankles
CORE_LANDMARKS       = [11, 12, 23, 24]             # shoulders + hips

# Map exercise folder names → which landmark groups matter most
EXERCISE_LANDMARK_MAP = {
    # Upper body dominant
    "barbell biceps curl":  UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "bench press":          UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "hammer curl":          UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "incline bench press":  UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "lat pulldown":         UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "lateral raise":        UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "pull Up":              UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "shoulder press":       UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "t bar row":            UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "tricep dips":          UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "tricep Pushdown":      UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    # Lower body dominant
    "squat":                LOWER_BODY_LANDMARKS + CORE_LANDMARKS,
    "deadlift":             LOWER_BODY_LANDMARKS + UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "romanian deadlift":    LOWER_BODY_LANDMARKS + UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    "hip thrust":           LOWER_BODY_LANDMARKS + CORE_LANDMARKS,
    "leg extension":        LOWER_BODY_LANDMARKS + CORE_LANDMARKS,
    "leg raises":           LOWER_BODY_LANDMARKS + CORE_LANDMARKS,
    # Core
    "plank":                UPPER_BODY_LANDMARKS + LOWER_BODY_LANDMARKS + CORE_LANDMARKS,
    "russian twist":        UPPER_BODY_LANDMARKS + CORE_LANDMARKS,
    # Full-body
    "push-up":              UPPER_BODY_LANDMARKS + LOWER_BODY_LANDMARKS + CORE_LANDMARKS,
}


# ── Validator ──────────────────────────────────────────────────────────────
def validate_video(video_path: Path, key_landmarks: list, pose) -> dict:
    """
    Returns a dict with quality metrics for one video.
    """
    result = {
        "path": str(video_path),
        "total_frames": 0,
        "sampled_frames": 0,
        "pose_detected": 0,
        "pose_rate": 0.0,
        "avg_key_visibility": 0.0,
        "duration_sec": 0.0,
        "usable_frames": 0,
        "status": "ok",
        "reason": "",
    }

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        result["status"] = "bad"
        result["reason"] = "Cannot open file"
        return result

    fps        = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_f    = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration   = total_f / fps if fps > 0 else 0
    result["total_frames"]  = total_f
    result["duration_sec"]  = round(duration, 2)

    if duration < MIN_VIDEO_SECONDS:
        cap.release()
        result["status"] = "bad"
        result["reason"] = f"Too short ({duration:.1f}s < {MIN_VIDEO_SECONDS}s)"
        return result

    if total_f < MIN_USABLE_FRAMES:
        cap.release()
        result["status"] = "bad"
        result["reason"] = f"Too few frames ({total_f})"
        return result

    # ------------------------------------------------------------------
    # Sample frames evenly across the video
    # ------------------------------------------------------------------
    sample_size    = min(SAMPLE_FRAMES, total_f)
    sample_indices = [int(i * total_f / sample_size) for i in range(sample_size)]

    visibility_scores = []
    pose_detected_cnt = 0

    for fi in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, frame = cap.read()
        if not ret:
            continue

        result["sampled_frames"] += 1

        # Resize for speed
        h, w = frame.shape[:2]
        if w > 640:
            scale = 640 / w
            frame = cv2.resize(frame, (640, int(h * scale)))

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)

        if res.pose_landmarks:
            pose_detected_cnt += 1
            # Check key landmark visibility
            lms = res.pose_landmarks.landmark
            vis = [lms[idx].visibility for idx in key_landmarks if idx < len(lms)]
            if vis:
                visibility_scores.append(sum(vis) / len(vis))

    cap.release()

    if result["sampled_frames"] == 0:
        result["status"] = "bad"
        result["reason"] = "No readable frames"
        return result

    pose_rate       = pose_detected_cnt / result["sampled_frames"]
    avg_vis         = sum(visibility_scores) / len(visibility_scores) if visibility_scores else 0.0
    usable_frames   = int(pose_detected_cnt)

    result["pose_detected"]       = pose_detected_cnt
    result["pose_rate"]           = round(pose_rate, 3)
    result["avg_key_visibility"]  = round(avg_vis, 3)
    result["usable_frames"]       = usable_frames

    # ------------------------------------------------------------------
    # Decide status
    # ------------------------------------------------------------------
    reasons = []
    if pose_rate < MIN_POSE_DETECTION_RATE:
        reasons.append(f"Low pose detection ({pose_rate*100:.0f}% < {MIN_POSE_DETECTION_RATE*100:.0f}%)")
    if avg_vis < MIN_KEY_VISIBILITY and visibility_scores:
        reasons.append(f"Key landmarks poorly visible ({avg_vis*100:.0f}% < {MIN_KEY_VISIBILITY*100:.0f}%)")
    if usable_frames < MIN_USABLE_FRAMES:
        reasons.append(f"Too few usable frames ({usable_frames} < {MIN_USABLE_FRAMES})")

    if reasons:
        result["status"] = "bad"
        result["reason"] = " | ".join(reasons)
    else:
        result["status"] = "ok"

    return result


# ── Main ───────────────────────────────────────────────────────────────────
def main(delete_bad: bool):
    print("=" * 65)
    print("  FITNESS DATASET VALIDATOR")
    print(f"  Mode: {'DELETE bad videos' if delete_bad else 'DRY-RUN (report only)'}")
    print("=" * 65)

    if not DATASET_DIR.exists():
        print(f"❌ Dataset folder not found: {DATASET_DIR.resolve()}")
        sys.exit(1)

    pose = mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.4,
    )

    all_results = []
    exercise_stats = defaultdict(lambda: {"total": 0, "bad": 0, "ok": 0})
    total_bad = 0
    total_ok  = 0

    # Walk dataset/<exercise>/<correct|wrong>/*.mp4
    exercise_dirs = sorted([d for d in DATASET_DIR.iterdir()
                            if d.is_dir() and not d.name.startswith("_")])

    for ex_dir in exercise_dirs:
        ex_name = ex_dir.name
        key_landmarks = EXERCISE_LANDMARK_MAP.get(ex_name,
                        UPPER_BODY_LANDMARKS + CORE_LANDMARKS)

        print(f"\n📂 {ex_name}")

        for label in ["correct", "wrong"]:
            label_dir = ex_dir / label
            if not label_dir.exists():
                continue

            videos = sorted(label_dir.glob("*.mp4"))
            if not videos:
                continue

            print(f"   ▶ {label} ({len(videos)} videos)")

            for vp in videos:
                r = validate_video(vp, key_landmarks, pose)
                r["exercise"] = ex_name
                r["label"]    = label
                all_results.append(r)
                exercise_stats[ex_name]["total"] += 1

                icon = "✅" if r["status"] == "ok" else "❌"
                pose_pct = f"{r['pose_rate']*100:.0f}%"
                vis_pct  = f"{r['avg_key_visibility']*100:.0f}%"

                print(f"      {icon} {vp.name:<50s} pose={pose_pct:>4s}  vis={vis_pct:>4s}  {r['reason']}")

                if r["status"] == "bad":
                    exercise_stats[ex_name]["bad"] += 1
                    total_bad += 1

                    if delete_bad:
                        # Move to rejected folder
                        dest_dir = REJECTED_DIR / ex_name / label
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(vp), str(dest_dir / vp.name))
                        print(f"         → Moved to {dest_dir / vp.name}")
                else:
                    exercise_stats[ex_name]["ok"] += 1
                    total_ok += 1

    pose.close()

    # ------------------------------------------------------------------
    # Save CSV report
    # ------------------------------------------------------------------
    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["exercise", "label", "path", "status", "reason",
                      "duration_sec", "total_frames", "sampled_frames",
                      "pose_detected", "pose_rate", "avg_key_visibility",
                      "usable_frames"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("  VALIDATION SUMMARY")
    print("=" * 65)
    print(f"  {'Exercise':<30s} {'Total':>6} {'OK':>5} {'Bad':>5}")
    print(f"  {'-'*30} {'-'*6} {'-'*5} {'-'*5}")
    for ex_name in sorted(exercise_stats):
        s = exercise_stats[ex_name]
        flag = " ⚠️" if s["bad"] > 0 else ""
        print(f"  {ex_name:<30s} {s['total']:>6} {s['ok']:>5} {s['bad']:>5}{flag}")

    print(f"\n  TOTAL: {total_ok + total_bad} videos  |  ✅ OK: {total_ok}  |  ❌ Bad: {total_bad}")
    print(f"\n  📄 Full report saved to: {REPORT_CSV.resolve()}")

    if total_bad > 0 and not delete_bad:
        print(f"\n  ⚠️  Run with --delete to move {total_bad} bad videos to {REJECTED_DIR}/")
    elif total_bad > 0 and delete_bad:
        print(f"\n  🗑️  {total_bad} bad videos moved to {REJECTED_DIR}/")
        print(f"  ✅ Dataset is now cleaner — please retrain the model!")
    else:
        print(f"\n  ✅ Dataset looks clean — no bad videos found.")

    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fitness Dataset Validator")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Move bad videos to dataset/_rejected/ (default: dry-run only)"
    )
    args = parser.parse_args()
    main(delete_bad=args.delete)
