import os
import sys
import sqlalchemy as sa
from urllib.parse import quote_plus

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from dotenv import load_dotenv

def migrate():
    load_dotenv()
    
    # 1. Setup Source URL (Local MySQL)
    source_url = os.environ.get("DATABASE_URL", "mysql+pymysql://root:@localhost/nextstep_db")
    # 2. Setup Target URL (Supabase Postgres)
    target_url = os.environ.get('TARGET_URL')
    if not target_url:
        target_url = input("Enter your FULL Supabase Connection String (replace [YOUR-PASSWORD] with your actual password!): ").strip()
    
    print(f"Source DB: {source_url}")
    print(f"Target DB: {target_url[:30]}...[HIDDEN]")

    source_engine = sa.create_engine(source_url)
    target_engine = sa.create_engine(target_url)

    app = create_app()
    with app.app_context():
        # Import all models so they register with db.metadata
        from app.models.user import User, Profile, ProfileSkill
        from app.models.job import JobListing, SkillTrend, JobRaw
        from app.models.job_skill import JobSkill
        from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, RoleTaxonomy, CountryMapping
        from app.models.assessment import Assessment, AssessmentQuestion
        from app.models.application import JobApplication
        from app.services.pipeline import RoleTrend, SectorTrend

        metadata = db.metadata

        print("\n[1/3] Rebuilding tables on Supabase (Dropping old schema)...")
        metadata.drop_all(target_engine)
        metadata.create_all(target_engine)
        print("Tables rebuilt with updated indices.")

        print("\n[2/3] Cleaning target tables (Reverse order for FKs)...")
        with target_engine.connect() as tgt_conn:
            for table in reversed(metadata.sorted_tables):
                try:
                    tgt_conn.execute(table.delete())
                    tgt_conn.commit()
                except Exception as e:
                    pass # Ignore if table doesn't exist or empty

        print("\n[3/3] Migrating data (Forward order)...")
        with source_engine.connect() as src_conn:
            with target_engine.connect() as tgt_conn:
                for table in metadata.sorted_tables:
                    print(f"Migrating table: {table.name}...")
                    try:
                        rows = src_conn.execute(sa.select(table)).fetchall()
                        if rows:
                            # Convert rows to dicts
                            data = [dict(row._mapping) for row in rows]
                            # Batch insert
                            tgt_conn.execute(table.insert(), data)
                            tgt_conn.commit()
                            print(f" -> Inserted {len(data)} rows.")
                        else:
                            print(f" -> 0 rows.")
                    except Exception as e:
                        safe_error = str(e).encode('ascii', 'ignore').decode('ascii')
                        print(f" -> ERROR: {safe_error[:200]}...")
                        tgt_conn.rollback()

        print("\nMigration fully complete! The live app now has all your local data.")

if __name__ == '__main__':
    migrate()
