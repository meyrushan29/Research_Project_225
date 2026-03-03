import os
import sys

# Ensure import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal, engine, Base
from core.models import ExerciseMetadata

# Create tables if not exist
Base.metadata.create_all(bind=engine)

data = [
    {"name": "barbell biceps curl", "body_part": "Biceps", "secondary_body_part": "Forearms", "target_category": "Upper Body Pull"},
    {"name": "bench press", "body_part": "Chest (Pectorals)", "secondary_body_part": "Triceps, Front Shoulders", "target_category": "Upper Body Push"},
    {"name": "deadlift", "body_part": "Glutes, Hamstrings", "secondary_body_part": "Lower Back, Core, Traps", "target_category": "Lower Body"},
    {"name": "hammer curl", "body_part": "Biceps (Brachialis)", "secondary_body_part": "Forearms", "target_category": "Upper Body Pull"},
    {"name": "hip thrust", "body_part": "Glutes", "secondary_body_part": "Hamstrings, Core", "target_category": "Lower Body"},
    {"name": "incline bench press", "body_part": "Upper Chest", "secondary_body_part": "Shoulders, Triceps", "target_category": "Upper Body Push"},
    {"name": "lat pulldown", "body_part": "Lats (Back)", "secondary_body_part": "Biceps", "target_category": "Upper Body Pull"},
    {"name": "lateral raise", "body_part": "Side Shoulders (Deltoids)", "secondary_body_part": "Upper Traps", "target_category": "Upper Body Push"},
    {"name": "leg extension", "body_part": "Quadriceps", "secondary_body_part": "None major", "target_category": "Lower Body"},
    {"name": "leg raises", "body_part": "Lower Abs", "secondary_body_part": "Hip Flexors", "target_category": "Core"},
    {"name": "plank", "body_part": "Core", "secondary_body_part": "Shoulders, Glutes", "target_category": "Core"},
    {"name": "pull up", "body_part": "Lats (Back)", "secondary_body_part": "Biceps, Core", "target_category": "Upper Body Pull"},
    {"name": "push up", "body_part": "Chest", "secondary_body_part": "Triceps, Shoulders, Core", "target_category": "Upper Body Push"},
    {"name": "romanian deadlift", "body_part": "Hamstrings", "secondary_body_part": "Glutes, Lower Back", "target_category": "Lower Body"},
    {"name": "russian twist", "body_part": "Obliques", "secondary_body_part": "Core", "target_category": "Core"},
    {"name": "shoulder press", "body_part": "Shoulders (Deltoids)", "secondary_body_part": "Triceps", "target_category": "Upper Body Push"},
    {"name": "squat", "body_part": "Quadriceps, Glutes", "secondary_body_part": "Hamstrings, Core", "target_category": "Lower Body"},
    {"name": "t bar row", "body_part": "Mid Back", "secondary_body_part": "Biceps, Rear Shoulders", "target_category": "Upper Body Pull"},
    {"name": "tricep dips", "body_part": "Triceps", "secondary_body_part": "Chest, Shoulders", "target_category": "Upper Body Push"},
    {"name": "tricep pushdown", "body_part": "Triceps", "secondary_body_part": "None major", "target_category": "Upper Body Push"},
]

def seed():
    db = SessionLocal()
    count = 0
    for item in data:
        ex = db.query(ExerciseMetadata).filter_by(name=item["name"]).first()
        if ex:
            ex.body_part = item["body_part"]
            ex.secondary_body_part = item["secondary_body_part"]
            ex.target_category = item["target_category"]
        else:
            new_ex = ExerciseMetadata(
                name=item["name"],
                body_part=item["body_part"],
                secondary_body_part=item["secondary_body_part"],
                target_category=item["target_category"]
            )
            db.add(new_ex)
        count += 1
    db.commit()
    db.close()
    print(f"Seeded {count} exercises into metadata.")

if __name__ == "__main__":
    seed()
