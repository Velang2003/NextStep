"""
Consumer script to process raw job postings from the JobRaw staging table.
Developer triggers this manually for now: python process_raw_jobs.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from app import create_app, db
from app.models.job import JobRaw, JobListing
from app.models.job_skill import JobSkill
from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, RoleTaxonomy
from app.services.data_normalizer import extract_skills, classify_department, normalize_role

def run_consumer():
    app = create_app()
    with app.app_context():
        # 1. Pre-fetch Taxonomy and existing listings into memory
        print("[Consumer] Pre-fetching taxonomy and mapping data...")
        from app.models.taxonomy import RoleSkill
        sectors_map = {s.name: s.id for s in SectorTaxonomy.query.all()}
        roles_map = {r.title: r.id for r in RoleTaxonomy.query.all()}
        skills_map = {s.canonical_name: s.id for s in SkillTaxonomy.query.all()}
        
        # Maps (source, source_id) -> JobListing.id
        existing_listings = {
            (jl.source, jl.source_id): jl.id 
            for jl in JobListing.query.with_entities(JobListing.id, JobListing.source, JobListing.source_id).all()
        }

        # Load Role-Skill associations for validation
        role_skill_associations = {}
        rs_rows = RoleSkill.query.all()
        for rs in rs_rows:
            if rs.role_id not in role_skill_associations:
                role_skill_associations[rs.role_id] = set()
            role_skill_associations[rs.role_id].add(rs.skill_id)

        # We allow re-processing of specific jobs if needed, but default to unprocessed
        raw_jobs = JobRaw.query.filter_by(is_processed=False).all()
        total_found = len(raw_jobs)
        print(f"[Consumer] Found {total_found} unprocessed raw jobs.")

        batch_size = 100
        for i, raw in enumerate(raw_jobs):
            payload = raw.raw_payload
            
            title = payload.get('title', '')
            dept = payload.get('department', '')
            desc = payload.get('description', '') or ''
            
            sector_name = classify_department(title, dept)
            role_name = normalize_role(title)
            
            sector_id = sectors_map.get(sector_name)
            role_id = roles_map.get(role_name)

            # Check for existing listing to Update instead of Insert
            listing_id = existing_listings.get((raw.source, raw.source_id))
            
            if listing_id:
                # Update existing listing
                listing = JobListing.query.get(listing_id)
                listing.title = title
                listing.department = dept
                listing.sector_id = sector_id
                listing.role_id = role_id
                
                # Clear existing skills to refresh with precision
                JobSkill.query.filter_by(job_id=listing_id).delete()
            else:
                # Create new listing
                listing = JobListing(
                    source=raw.source,
                    source_id=raw.source_id,
                    company=payload.get('company'),
                    title=title,
                    department=dept,
                    location=payload.get('location'),
                    country=payload.get('country'),
                    employment_type=payload.get('employment_type', 'Full-time'),
                    remote=payload.get('remote', False),
                    description=desc,
                    url=payload.get('url'),
                    sector_id=sector_id,
                    role_id=role_id
                )
                db.session.add(listing)
                db.session.flush() # To get listing.id
                listing_id = listing.id

            # --- Precision Skill Extraction ---
            detected_skill_names = extract_skills(f"{title} {desc}")
            allowed_skill_ids = role_skill_associations.get(role_id, set()) if role_id else set()
            
            for skill_name in detected_skill_names:
                skill_id = skills_map.get(skill_name)
                if not skill_id: continue
                
                is_valid = False
                # A) Strict taxonomy match
                if skill_id in allowed_skill_ids: is_valid = True
                # B) Title match
                elif skill_name.lower() in title.lower(): is_valid = True
                # C) High frequency
                elif desc.lower().count(skill_name.lower()) >= 3: is_valid = True
                # D) Unmapped fallback
                elif not role_id: is_valid = True

                if is_valid:
                    db.session.add(JobSkill(job_id=listing_id, skill_id=skill_id, proficiency_level='medium'))

            raw.is_processed = True

            if (i + 1) % batch_size == 0:
                db.session.commit()
                print(f"[Consumer] Processed {i + 1}/{total_found} jobs...")

        db.session.commit()
        print("[Consumer] Processing complete. Recomputing trends...")
        from app.services.pipeline import _recompute_skill_trends, _recompute_role_trends, _recompute_sector_trends
        _recompute_skill_trends()
        _recompute_role_trends()
        _recompute_sector_trends()

if __name__ == '__main__':
    run_consumer()
