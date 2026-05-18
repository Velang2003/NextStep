import os
import sys

# Add parent directory to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.taxonomy import SkillTaxonomy, SkillAlias, RoleSkill
from app.models.job import SkillTrend, JobListing

def clean_skills():
    app = create_app()
    with app.app_context():
        # Extracted directly via Phi-3.5 prompt analysis offline to prevent inference hang on this machine
        noisy_skills_to_delete = [
            'Communication', 'Innovation', 'Planning', 'Leadership', 'Execution', 
            'Testing', 'Security', 'Reporting', 'Compliance', 'Analytics', 'Mentoring',
            'Cybersecurity', 'Application Security', 'Observability', 'Troubleshooting',
            'Architecture', 'Agile Methodologies', 'Agile', 'Software Development',
            'Continuous Integration', 'Integration', 'System Design'
        ]
        
        print(f"Starting purge of {len(noisy_skills_to_delete)} noisy/soft skills from taxonomy...", flush=True)
        
        deleted_count = 0
        for name in noisy_skills_to_delete:
            skill = SkillTaxonomy.query.filter(db.func.lower(SkillTaxonomy.canonical_name) == name.lower()).first()
            if skill:
                print(f"Deleting: {skill.canonical_name}", flush=True)
                
                # Delete dependencies manually to prevent cascade issues
                SkillAlias.query.filter_by(skill_id=skill.id).delete()
                RoleSkill.query.filter_by(skill_id=skill.id).delete()
                
                SkillTrend.query.filter(db.func.lower(SkillTrend.skill) == name.lower()).delete()
                
                db.session.delete(skill)
                deleted_count += 1
                
        db.session.commit()
        print(f"\nSuccessfully deleted {deleted_count} noisy skills from the database.", flush=True)
        
        # Finally, we should recompute the Skill Trends so the graphs update immediately
        from app.services.pipeline import _recompute_skill_trends
        print("Recomputing skill trends...", flush=True)
        _recompute_skill_trends()
        print("Done!", flush=True)

if __name__ == '__main__':
    clean_skills()
