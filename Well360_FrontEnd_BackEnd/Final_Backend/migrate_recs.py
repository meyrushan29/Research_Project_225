import sqlite3
import json
import os
import sys

# Define base dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hydration", "hydration_app.db")
JSON_PATH = os.path.join(BASE_DIR, "fitness", "recommendations.json")

def migrate():
    # 1. Provide columns
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            c.execute("ALTER TABLE exercise_metadata ADD COLUMN correct_tips JSON")
            print("Added correct_tips column")
        except sqlite3.OperationalError:
            print("correct_tips column already exists")
            
        try:
            c.execute("ALTER TABLE exercise_metadata ADD COLUMN wrong_tips JSON")
            print("Added wrong_tips column")
        except sqlite3.OperationalError:
            print("wrong_tips column already exists")
            
        conn.commit()
    except Exception as e:
        print(f"Error altering table: {e}")
        return

    # 2. Read JSON
    if not os.path.exists(JSON_PATH):
        print(f"JSON not found at {JSON_PATH}")
        return
        
    with open(JSON_PATH, "r") as f:
        recs = json.load(f)
        
    # 3. Update records
    for ex_name, data in recs.items():
        correct = data.get("correct", [])
        wrong = data.get("wrong", [])
        db_name = ex_name.replace("_", " ")

        c.execute(
            "UPDATE exercise_metadata SET correct_tips = ?, wrong_tips = ? WHERE name = ?",
            (json.dumps(correct), json.dumps(wrong), db_name)
        )
        if c.rowcount > 0:
            print(f"Updated {db_name}")
        else:
            print(f"No existing record for {db_name} found to update.")
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
