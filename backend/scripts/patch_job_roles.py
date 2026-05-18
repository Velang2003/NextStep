import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.job import JobListing
from app.models.taxonomy import RoleTaxonomy, RoleAlias

def patch_job_roles():
    app = create_app()
    with app.app_context():
        print("[Patcher] Starting Job-Role Mapping Patch...")
        
        # 1. Fetch Taxonomy into memory for speed
        roles = RoleTaxonomy.query.all()
        # { name_lower: role_id }
        taxonomy_map = {}
        for r in roles:
            taxonomy_map[r.title.lower()] = r.id
            for alias in r.aliases:
                taxonomy_map[alias.name.lower()] = r.id
        
        # 2. Find jobs without role_id
        unmapped_jobs = JobListing.query.filter(JobListing.role_id == None).all()
        total_unmapped = len(unmapped_jobs)
        print(f"[Patcher] Found {total_unmapped} unmapped jobs.")
        
        match_count = 0
        batch_size = 500
        
        for i, job in enumerate(unmapped_jobs):
            title_lower = job.title.lower()
            
            # Simple substring matching against canonical titles and aliases
            best_id = None
            best_match_len = 0
            
            for name, rid in taxonomy_map.items():
                if name in title_lower and len(name) > best_match_len:
                    best_id = rid
                    best_match_len = len(name)
            
            if best_id:
                job.role_id = best_id
                match_count += 1
                
            if (i + 1) % batch_size == 0:
                db.session.commit()
                print(f"[Patcher] Processed {i + 1}/{total_unmapped}...")

        db.session.commit()
        print(f"[Patcher] Successfully mapped {match_count} additional jobs.")

if __name__ == '__main__':
    patch_job_roles()
