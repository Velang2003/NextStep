"""
Initialize / reset the database tables and seed taxonomy data.
Run: python init_db.py
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db


def init():
    app = create_app()
    with app.app_context():
        from app.models.user import User, Profile, ProfileSkill
        from app.models.job import JobListing, SkillTrend, JobRaw
        from app.models.job_skill import JobSkill
        from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, RoleTaxonomy, CountryMapping
        from app.models.assessment import Assessment, AssessmentQuestion
        from app.models.application import JobApplication
        from app.services.pipeline import RoleTrend, SectorTrend

        db.drop_all()
        db.create_all()
        print("[Init] All tables dropped and created.")

    # Seed taxonomy
    from seed_taxonomy import seed
    seed()


if __name__ == '__main__':
    init()
