"""
Migration: Add pending_roles table.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS pending_roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    suggested_sector VARCHAR(100),
                    source VARCHAR(60),
                    source_detail VARCHAR(250),
                    status VARCHAR(20) DEFAULT 'pending',
                    admin_note TEXT,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP NULL,
                    reviewed_by VARCHAR(120)
                )
            """))
            conn.commit()
            print("OK: Created pending_roles table.")
        except Exception as e:
            print(f"ERROR: {e}")
