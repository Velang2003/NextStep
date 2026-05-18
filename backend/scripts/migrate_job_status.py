"""Migrate job_listings table: add status and last_seen_at columns."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        migrations = [
            "ALTER TABLE job_listings ADD COLUMN status VARCHAR(20) DEFAULT 'active'",
            "ALTER TABLE job_listings ADD COLUMN last_seen_at DATETIME",
            "UPDATE job_listings SET status='active', last_seen_at=fetched_at WHERE status IS NULL",
            "CREATE INDEX IF NOT EXISTS ix_job_listings_status ON job_listings(status)",
        ]
        for sql in migrations:
            try:
                conn.execute(db.text(sql))
                conn.commit()
                print(f"OK: {sql[:60]}...")
            except Exception as e:
                print(f"SKIP ({e.__class__.__name__}): {sql[:60]}...")

    db.create_all()
    from app.models.job import JobListing
    total  = JobListing.query.count()
    active = JobListing.query.filter_by(status='active').count()
    print(f"\nTotal listings: {total} | Active: {active}")
