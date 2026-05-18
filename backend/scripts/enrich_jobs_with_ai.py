import os
import sys
import time
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.job import JobListing
from app.models.job_skill import JobSkill
from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, RoleTaxonomy, PendingSkill, RoleSkill, PendingRole
from app.services.ai_service import ai_svc

def enrich_jobs():
    app = create_app()
    with app.app_context():
        # 1. Identify jobs that need AI help:
        # - Sector is 'Other' or NULL
        # - Role is NULL or not matched to taxonomy
        # - Not already AI enriched
        
        other_sector = SectorTaxonomy.query.filter_by(name='Other').first()
        other_sector_id = other_sector.id if other_sector else None

        jobs_to_enrich = JobListing.query.filter(
            (JobListing.sector_id == None) | (JobListing.sector_id == other_sector_id) | (JobListing.role_id == None),
            JobListing.is_ai_enriched == False,
            JobListing.status == 'active'
        ).limit(20).all() # Smaller batch for local LLM or API quotas

        if not jobs_to_enrich:
            print("[AI Enrich] No jobs found needing enrichment.")
            return

        print(f"[AI Enrich] Found {len(jobs_to_enrich)} jobs to enrich using Gemini...")

        # Pre-load taxonomy for faster matching
        sectors_map = {s.name.lower(): s.id for s in SectorTaxonomy.query.all()}
        roles_map = {r.title.lower(): r.id for r in RoleTaxonomy.query.all()}
        skills_map = {s.canonical_name.lower(): s.id for s in SkillTaxonomy.query.all()}

        for job in jobs_to_enrich:
            safe_title = (job.title or "").encode('ascii', 'ignore').decode()
            safe_company = (job.company or "").encode('ascii', 'ignore').decode()
            print(f"[AI Enrich] Processing: {safe_title} @ {safe_company}...")
            
            # Call Gemini AI for classification
            ai_data = ai_svc.classify_job(job.title, job.description)
            if not ai_data:
                print(f"  [!] AI failed for job {job.id}")
                continue

            ai_sector = ai_data.get('sector', '').strip()
            ai_role = ai_data.get('role', '').strip()
            ai_skills = ai_data.get('skills', [])

            # Update Sector
            if ai_sector:
                s_id = sectors_map.get(ai_sector.lower())
                if s_id:
                    job.sector_id = s_id
                else:
                    # New sector detected! In a real pro app, we might add this to a PendingSector table.
                    pass

            # Update Role
            if ai_role:
                r_id = roles_map.get(ai_role.lower())
                if r_id:
                    job.role_id = r_id
                else:
                    # New role! Add to PendingRole queue
                    existing_pending_role = PendingRole.query.filter_by(title=ai_role).first()
                    if not existing_pending_role:
                        db.session.add(PendingRole(
                            title=ai_role,
                            suggested_sector=ai_sector,
                            source='gemini',
                            source_detail=f"{job.title} @ {job.company}"
                        ))

            # Process Skills
            if ai_skills:
                # Get current skills to avoid duplicates
                current_skill_ids = {js.skill_id for js in job.job_skills}
                
                for sk_name in ai_skills:
                    sk_id = skills_map.get(sk_name.lower())
                    if sk_id:
                        if sk_id not in current_skill_ids:
                            db.session.add(JobSkill(job_id=job.id, skill_id=sk_id, proficiency_level='high'))
                            current_skill_ids.add(sk_id)
                    else:
                        # New skill! Add to Pending queue for admin approval
                        existing_pending = PendingSkill.query.filter_by(name=sk_name).first()
                        if not existing_pending:
                            db.session.add(PendingSkill(
                                name=sk_name,
                                source='gemini',
                                suggested_category='Technical',
                                suggested_role_id=job.role_id,
                                source_detail=f"Job: {job.title} @ {job.company}"
                            ))

            job.is_ai_enriched = True
            db.session.commit()
            print(f"  [OK] Updated. Sector: {ai_sector}, Role: {ai_role}, Skills: {len(ai_skills)}")
            
            # Rate limiting sleep (essential for free APIs, good for local heat)
            time.sleep(2)  # Rate limiting for Gemini API

        print("[AI Enrich] Batch complete.")

if __name__ == '__main__':
    enrich_jobs()
