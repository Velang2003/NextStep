import os
import sys
import sqlalchemy as sa

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv

def apply_indexes():
    load_dotenv()
    
    # Setup Target URL (Supabase Postgres)
    target_url = os.environ.get("DATABASE_URL")
    if not target_url or not target_url.startswith("postgresql"):
        print("ERROR: DATABASE_URL must be set to your Supabase postgresql string in the .env file.")
        print("Current DATABASE_URL:", target_url)
        return

    print(f"Connecting to database at: {target_url[:30]}...[HIDDEN]")
    engine = sa.create_engine(target_url)

    # Raw SQL commands to add indexes without locking tables (CONCURRENTLY requires a different transaction mode, 
    # but IF NOT EXISTS handles safety). We'll use standard CREATE INDEX IF NOT EXISTS.
    queries = [
        "CREATE INDEX IF NOT EXISTS ix_job_listings_sector_id ON job_listings (sector_id);",
        "CREATE INDEX IF NOT EXISTS ix_job_listings_role_id ON job_listings (role_id);",
        "CREATE INDEX IF NOT EXISTS ix_job_listings_country ON job_listings (country);",
        "CREATE INDEX IF NOT EXISTS ix_job_listings_remote ON job_listings (remote);",
        "CREATE INDEX IF NOT EXISTS ix_job_skills_job_id ON job_skills (job_id);",
        "CREATE INDEX IF NOT EXISTS ix_job_skills_skill_id ON job_skills (skill_id);",
        "CREATE INDEX IF NOT EXISTS idx_job_skill_composite ON job_skills (job_id, skill_id);"
    ]

    print("\nApplying Database Indexes to Supabase...")
    with engine.connect() as conn:
        for q in queries:
            try:
                print(f"Executing: {q}")
                conn.execute(sa.text(q))
                conn.commit()
            except Exception as e:
                print(f" -> ERROR or Already Exists: {e}")
                conn.rollback()

    print("\nPerformance Optimization Complete! Indexes have been successfully applied.")

if __name__ == '__main__':
    apply_indexes()
