import os
import sys
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import _db_dir

db_path = _db_dir / 'hydration_app.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("ALTER TABLE exercise_metadata ADD COLUMN secondary_body_part VARCHAR")
except Exception as e:
    print(e)
    
try:
    c.execute("ALTER TABLE exercise_metadata ADD COLUMN target_category VARCHAR")
except Exception as e:
    print(e)

conn.commit()
conn.close()
print("ALTER TABLE statements executed.")
