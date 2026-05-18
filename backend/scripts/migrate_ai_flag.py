"""
Migration: Add is_ai_enriched column to job_listings.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text("ALTER TABLE job_listings ADD COLUMN is_ai_enriched BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("OK: Added is_ai_enriched column.")
        except Exception as e:
            print(f"SKIP: {e}")
