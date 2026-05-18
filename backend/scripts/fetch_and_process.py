"""
fetch_and_process.py
====================
Wipes all job data and re-fetches fresh data from ATS APIs.

Step 0 — wipe_job_tables()  : Clears job_skills, job_listings, job_raw,
                               skill_trends, role_trends, sector_trends.
Step 1 — run_pipeline()     : Calls Greenhouse, Lever & Ashby APIs → inserts
                               fresh raw payloads into `job_raw` staging table.
Step 2 — run_consumer()     : Reads unprocessed rows from `job_raw`, normalises
                               them against the taxonomy, writes to `job_listings`
                               + `job_skills`, then recomputes trend tables.

Usage:
    venv\\Scripts\\python.exe fetch_and_process.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.services.pipeline import run_pipeline


# ---------------------------------------------------------------------------
# Wipe helpers
# ---------------------------------------------------------------------------

JOB_TABLES = [
    'job_skills',       # child of job_listings and skill_taxonomy
    'job_listings',     # child of sector_taxonomy / role_taxonomy
    'job_raw',          # staging table
    'skill_trends',     # computed aggregates
    'role_trends',
    'sector_trends',
]


def wipe_job_tables():
    """Delete all rows from job-related tables, bypassing FK checks."""
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in JOB_TABLES:
            result = conn.execute(db.text(f"DELETE FROM `{table}`"))
            print(f"[Wipe] {table}: {result.rowcount} rows deleted")
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        trans.commit()
    except Exception:
        trans.rollback()
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    app = create_app()
    with app.app_context():

        # ── Step 1: Fetch & smart-refresh (no wipe) ───────────────────────
        # Stale jobs are marked 'expired', not deleted.
        # Historical trend data is preserved for quarter-over-quarter comparison.
        print("=" * 55)
        print("STEP 1 — Smart Refresh (no data is deleted)")
        print("=" * 55)
        results = run_pipeline()
        print(f"\n[Summary] Fetched: {results['fetched']} | "
              f"New: {results['inserted']} | "
              f"Refreshed: {results['skipped']}")
        if results['errors']:
            print("[Warnings] Some sources had errors:")
            for e in results['errors']:
                print(f"  - {e}")

        # ── Step 2: Process new raw jobs ──────────────────────────────────
        print("\n" + "=" * 55)
        print("STEP 2 — Processing new raw jobs into job_listings")
        print("=" * 55)

    import process_raw_jobs
    process_raw_jobs.run_consumer()

    print("\n[Done] Smart refresh complete. Active jobs updated, history preserved.")



if __name__ == '__main__':
    main()

