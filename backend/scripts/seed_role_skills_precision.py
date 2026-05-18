import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.taxonomy import SkillTaxonomy, RoleTaxonomy, RoleSkill

def seed_role_skills_precision():
    app = create_app()
    with app.app_context():
        print("[Seeder] Starting High-Precision Role-Skill Seeding...")
        
        all_roles = RoleTaxonomy.query.all()
        all_skills = SkillTaxonomy.query.all()
        
        # 1. Define High-Precision Affinity Rules
        # Keywords map to allowed Skill Categories (the ones I just patched)
        AFFINITY_RULES = [
            # Technical Contexts
            {
                'keywords': ['software', 'engineer', 'developer', 'swe', 'architect'],
                'adds': ['System-Lang', 'Enterprise-Lang', 'Backend-Framework', 'Architecture', 'DevOps', 'API-REST', 'API-RPC', 'Database-Query', 'Database-Doc', 'Tool', 'Methodology', 'Soft Skill']
            },
            {
                'keywords': ['frontend', 'ui', 'ux', 'web'],
                'adds': ['Frontend-Framework', 'Web-Lang', 'Design', 'API-Graph', 'Tool', 'Soft Skill']
            },
            {
                'keywords': ['backend'],
                'adds': ['Backend-Framework', 'Enterprise-Lang', 'System-Lang', 'Database-Query', 'Database-Doc', 'API-REST', 'API-RPC', 'Architecture', 'Tool']
            },
            {
                'keywords': ['data', 'scientist', 'analyst', 'ml', 'ai'],
                'adds': ['Data-Lang', 'Data', 'AI/ML', 'Database-Query', 'Tool', 'Soft Skill']
            },
            {
                'keywords': ['devops', 'cloud', 'infrastructure', 'sre'],
                'adds': ['DevOps', 'Cloud', 'Infrastructure', 'System-Lang', 'Security', 'Architecture', 'Tool']
            },
            {
                'keywords': ['mobile', 'android', 'ios'],
                'adds': ['App-Lang', 'Mobile', 'Frontend-Framework', 'API-REST', 'Tool']
            },
            {
                'keywords': ['security', 'auditor', 'compliance'],
                'adds': ['Security', 'System-Lang', 'Infrastructure', 'Network', 'Soft Skill']
            },
            {
                'keywords': ['qa', 'test', 'automation'],
                'adds': ['Enterprise-Lang', 'Web-Lang', 'Tool', 'Methodology', 'Soft Skill']
            },
            {
                'keywords': ['game', 'unity', 'unreal', 'artist'],
                'adds': ['Engine', 'System-Lang', 'Design', 'Architecture', 'Tool']
            },
            
            # Business Contexts
            {
                'keywords': ['product', 'manager', 'scrum', 'owner'],
                'adds': ['Management', 'Methodology', 'Tool', 'Business', 'Soft Skill']
            },
            {
                'keywords': ['marketing', 'growth', 'content'],
                'adds': ['Marketing', 'Business', 'Tool', 'Soft Skill', 'Design']
            },
            {
                'keywords': ['sales', 'success', 'account', 'representative'],
                'adds': ['Business', 'Business-Tool', 'Soft Skill', 'Management']
            },
            {
                'keywords': ['finance', 'accountant', 'legal'],
                'adds': ['Finance', 'Business', 'Business-Tool', 'Soft Skill', 'Security']
            },
            {
                'keywords': ['hr', 'recruiter', 'people'],
                'adds': ['Soft Skill', 'Management', 'Business-Tool']
            }
        ]

        added_count = 0
        for role in all_roles:
            title_lower = role.title.lower()
            allowed_categories = set()
            
            # Apply all rules that match keywords in the role title
            matched_any = False
            for rule in AFFINITY_RULES:
                if any(kw in title_lower for kw in rule['keywords']):
                    allowed_categories.update(rule['adds'])
                    matched_any = True
            
            # Fallback for generic roles: just tools and soft skills
            if not matched_any:
                allowed_categories = {'Tool', 'Soft Skill', 'Methodology'}
            
            # Link skills that belong to the allowed categories
            relevant_skills = [s for s in all_skills if s.category in allowed_categories]
            for skill in relevant_skills:
                # Add link (uniqueness handled by DB constraint but good to check here)
                db.session.add(RoleSkill(role_id=role.id, skill_id=skill.id))
                added_count += 1

        db.session.commit()
        print(f"[Seeder] Successfully created {added_count} high-precision associations across {len(all_roles)} roles.")

if __name__ == '__main__':
    seed_role_skills_precision()
