import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.taxonomy import SkillTaxonomy, RoleTaxonomy, RoleSkill

def seed_role_skills():
    app = create_app()
    with app.app_context():
        print("[Seeder] Starting Role-Skill Association Seeding...")
        
        # 1. Fetch all roles and skills
        all_roles = RoleTaxonomy.query.all()
        all_skills = SkillTaxonomy.query.all()
        
        # 2. Categorize roles for mapping
        # Maps role keywords to allowed skill categories
        ROLE_CATEGORY_MAP = {
            'Engineering': ['Language', 'Frontend', 'Backend', 'DevOps', 'Cloud', 'Architecture', 'API', 'Database', 'Infrastructure', 'Tool', 'Methodology'],
            'Frontend': ['Frontend', 'Language', 'Tool', 'Methodology', 'API'],
            'Backend': ['Backend', 'Language', 'Database', 'API', 'Cloud', 'Architecture', 'DevOps', 'Tool', 'Methodology'],
            'Data': ['Data', 'AI/ML', 'Language', 'Database', 'Cloud', 'Tool'],
            'Design': ['Design', 'Tool', 'Methodology'],
            'Product': ['Management', 'Methodology', 'Tool', 'Soft Skill'],
            'Marketing': ['Marketing', 'Tool', 'Methodology', 'Soft Skill'],
            'Sales': ['Business', 'Soft Skill', 'Tool'],
            'Finance': ['Finance', 'Business', 'Tool'],
            'HR': ['Soft Skill', 'Tool']
        }

        # Clear existing mappings if any
        # RoleSkill.query.delete() 
        # (Actually we want to append or merge, but for a clean seed, we can clear)
        # db.session.commit()

        added_count = 0
        for role in all_roles:
            title_lower = role.title.lower()
            
            # Determine target skill categories for this role
            target_categories = []
            if any(k in title_lower for k in ['software', 'engineer', 'developer', 'swe']):
                target_categories = ROLE_CATEGORY_MAP['Engineering']
            if 'frontend' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Frontend']
            if 'backend' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Backend']
            if 'data' in title_lower or 'scientist' in title_lower or 'analyst' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Data']
            if 'design' in title_lower or 'ux' in title_lower or 'ui' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Design']
            if 'product' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Product']
            if 'marketing' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Marketing']
            if 'sales' in title_lower or 'account executive' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Sales']
            if 'finance' in title_lower or 'accountant' in title_lower:
                target_categories = ROLE_CATEGORY_MAP['Finance']
            
            # Fallback if no specific keyword matched
            if not target_categories:
                target_categories = ['Soft Skill', 'Tool', 'Methodology']

            # Match and Link
            relevant_skills = [s for s in all_skills if s.category in target_categories]
            for skill in relevant_skills:
                # Check for existing
                exists = RoleSkill.query.filter_by(role_id=role.id, skill_id=skill.id).first()
                if not exists:
                    db.session.add(RoleSkill(role_id=role.id, skill_id=skill.id))
                    added_count += 1

        db.session.commit()
        print(f"[Seeder] Successfully added {added_count} role-skill associations.")

if __name__ == '__main__':
    seed_role_skills()
