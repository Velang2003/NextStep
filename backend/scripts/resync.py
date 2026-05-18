from app import create_app, db
from app.models.job import JobListing, JobRaw, SkillTrend
from app.models.job_skill import JobSkill
from app.services.pipeline import run_pipeline, RoleTrend, SectorTrend
from process_raw_jobs import run_consumer

app = create_app()

with app.app_context():
    print("Clearing old dirty job data...")
    JobSkill.query.delete()
    JobListing.query.delete()
    JobRaw.query.delete()
    SkillTrend.query.delete()
    RoleTrend.query.delete()
    SectorTrend.query.delete()
    db.session.commit()
    print("Old jobs and trends cleared. Running fresh sync...")
    
    res = run_pipeline()
    print("Raw Sync complete:", res)
    
    print("Running worker to parse raw data to listings...")
    run_consumer()
    print("Full Sync Complete!")
