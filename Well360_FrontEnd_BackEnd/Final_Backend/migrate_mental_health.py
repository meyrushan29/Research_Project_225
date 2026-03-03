"""
migrate_mental_health.py
========================
One-time database migration for the improved Mental Health module.

Creates:
  - user_emotion_profiles   (new table — personalization engine)

Alters:
  - mental_health_analysis  adds  rec_shown_index  column

Safe to run multiple times (uses IF NOT EXISTS / checks before altering).

Usage:
    cd Final_Backend
    python migrate_mental_health.py
"""

import sys
import os

# Make sure we can import the project modules
sys.path.insert(0, os.path.dirname(__file__))

from core.database import engine, Base
from sqlalchemy import text, inspect

# Import ALL models so their metadata is registered on Base
from core import models  # noqa – side-effect: registers all ORM classes


def run_migration():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    print("=" * 60)
    print("  Mental Health DB Migration")
    print("=" * 60)

    # ── 1. Create new tables (safe if already exist) ─────────────────────────
    print("\n[1/2] Creating new tables (if they do not exist) …")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("      ✅  user_emotion_profiles table ready")

    # ── 2. Add rec_shown_index column to mental_health_analysis ──────────────
    print("\n[2/2] Adding rec_shown_index column to mental_health_analysis …")
    if "mental_health_analysis" in existing_tables:
        existing_cols = [
            col["name"]
            for col in inspector.get_columns("mental_health_analysis")
        ]
        if "rec_shown_index" not in existing_cols:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE mental_health_analysis "
                        "ADD COLUMN rec_shown_index INTEGER DEFAULT 0"
                    )
                )
                conn.commit()
            print("      ✅  rec_shown_index column added")
        else:
            print("      ℹ️   rec_shown_index column already exists — skipped")
    else:
        print("      ℹ️   mental_health_analysis table does not exist yet — will be created by create_all")

    print("\n" + "=" * 60)
    print("  Migration complete! ✅")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as exc:
        print(f"\n❌  Migration failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
