import sys
import os

# Add parent directory to path so we can import core.database and core.models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine, Base
from core.models import ExerciseMetadata

def seed_exercises():
    db = SessionLocal()
    
    # 20 Exercises - Names MUST MATCH result.get("exercise").lower().replace("_", " ") output
    # Config keys in exercise_config.py are lowercase with underscores.
    
    exercises = [
        {"name": "barbell biceps curl", "body_part": "Arms"},
        {"name": "bench press", "body_part": "Chest"},
        {"name": "deadlift", "body_part": "Back"}, 
        {"name": "hammer curl", "body_part": "Arms"},
        {"name": "hip thrust", "body_part": "Legs"}, 
        {"name": "incline bench press", "body_part": "Chest"},
        {"name": "lat pulldown", "body_part": "Back"},
        {"name": "lateral raise", "body_part": "Shoulders"},
        {"name": "leg extension", "body_part": "Legs"},
        {"name": "leg raises", "body_part": "Core"},
        {"name": "plank", "body_part": "Core"},
        {"name": "pull up", "body_part": "Back"},      # Fixed casing
        {"name": "push up", "body_part": "Chest"},      # Fixed dash to space
        {"name": "romanian deadlift", "body_part": "Legs"}, 
        {"name": "russian twist", "body_part": "Core"},
        {"name": "shoulder press", "body_part": "Shoulders"},
        {"name": "squat", "body_part": "Legs"},
        {"name": "t bar row", "body_part": "Back"},
        {"name": "tricep dips", "body_part": "Arms"}, 
        {"name": "tricep pushdown", "body_part": "Arms"}, # Fixed casing
    ]

    print("Seeding Exercise Metadata (Correction)...")
    
    added_count = 0
    updated_count = 0

    for ex_data in exercises:
        # Check if exists (case insensitive for safety, but we store exact)
        existing = db.query(ExerciseMetadata).filter(ExerciseMetadata.name == ex_data["name"]).first()
        
        if existing:
            # Update body part if needed
            if existing.body_part != ex_data["body_part"]:
                existing.body_part = ex_data["body_part"]
                updated_count += 1
        else:
            # Clean up potential duplicates with wrong casing/formatting?
            # It's unique constraint on name.
            # We might have "pull Up" existing. We should delete it if we want to be clean, 
            # OR we just add "pull up".
            
            # Let's try to find "close" matches and delete them?
            # Actually, standardizing strictly is safer.
            
            new_ex = ExerciseMetadata(name=ex_data["name"], body_part=ex_data["body_part"])
            db.add(new_ex)
            added_count += 1
            
    # Also delete incorrect legacy ones if possible?
    # e.g. "pull Up", "push-up", "tricep Pushdown"
    legacy_names = ["pull Up", "push-up", "tricep Pushdown"]
    deleted_count = 0
    for bad_name in legacy_names:
        bad_entry = db.query(ExerciseMetadata).filter(ExerciseMetadata.name == bad_name).first()
        if bad_entry:
            db.delete(bad_entry)
            deleted_count += 1

    try:
        db.commit()
        print(f"Success! Added: {added_count}, Updated: {updated_count}, Deleted Legacy: {deleted_count}")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_exercises()
