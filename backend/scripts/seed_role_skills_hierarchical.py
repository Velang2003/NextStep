import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.taxonomy import SkillTaxonomy, RoleTaxonomy, RoleSkill

def seed_role_skills_hierarchical():
    app = create_app()
    with app.app_context():
        print("[Seeder] Starting Hierarchical Role-Skill Seeding...")
        
        # Clear existing mappings for a fresh, precise start
        RoleSkill.query.delete()
        db.session.commit()
        
        all_roles = RoleTaxonomy.query.all()
        all_skills = SkillTaxonomy.query.all()
        
        # 1. Define Specialization-First Rules
        # If a role matches any keyword in 'triggers', ONLY those 'adds' are applied (plus Base).
        SPECIALIZATIONS = [
            {
                'triggers': ['frontend', 'ui', 'ux', 'web'],
                'forbidden': ['Data-Lang', 'System-Lang', 'App-Lang'],
                'adds': ['Frontend-Framework', 'Web-Lang', 'Design', 'API-Graph']
            },
            {
                'triggers': ['data', 'scientist', 'analyst', 'ml', 'ai'],
                'forbidden': ['Frontend-Framework', 'App-Lang'],
                'adds': ['Data-Lang', 'Data', 'AI/ML', 'Database-Query']
            },
            {
                'triggers': ['devops', 'cloud', 'infrastructure', 'sre'],
                'forbidden': ['Frontend-Framework', 'Design'],
                'adds': ['DevOps', 'Cloud', 'Infrastructure', 'System-Lang', 'Security']
            },
            {
                'triggers': ['mobile', 'android', 'ios'],
                'forbidden': ['Data-Lang', 'System-Lang'],
                'adds': ['App-Lang', 'Mobile', 'Frontend-Framework', 'API-REST']
            },
            {
                'triggers': ['security', 'auditor', 'compliance'],
                'adds': ['Security', 'System-Lang', 'Infrastructure', 'Network']
            }
        ]

        # 2. General Technical Role (Only applied if no specific Specialization is found)
        GENERAL_TECH = ['Enterprise-Lang', 'System-Lang', 'Backend-Framework', 'Architecture', 'DevOps', 'API-REST', 'API-RPC', 'Database-Query', 'Database-Doc']

        # 3. Base Set (Applied to all technical roles)
        BASE_TECH = ['Tool', 'Methodology', 'Soft Skill']
        
        # 4. Business/Non-Tech Set
        BUSINESS_SET = ['Business', 'Business-Tool', 'Marketing', 'Finance', 'Management', 'Soft Skill', 'Design']

        added_count = 0
        for role in all_roles:
            title_lower = role.title.lower()
            allowed_categories = set()
            forbidden_categories = set()
            
            is_technical = any(kw in title_lower for kw in ['software', 'engineer', 'developer', 'swe', 'architect', 'qa', 'test', 'data', 'ml', 'ai', 'frontend', 'backend', 'full stack', 'mobile', 'devops', 'cloud', 'security', 'game', 'embedded', 'hardware'])
            
            is_specialized = False
            for spec in SPECIALIZATIONS:
                if any(kw in title_lower for kw in spec['triggers']):
                    allowed_categories.update(spec['adds'])
                    forbidden_categories.update(spec.get('forbidden', []))
                    is_specialized = True
            
            if is_technical:
                allowed_categories.update(BASE_TECH)
                # If not specialized (like generic "Software Engineer"), give the full tech stack
                if not is_specialized or 'full stack' in title_lower or 'software engineer' in title_lower:
                    allowed_categories.update(GENERAL_TECH)
                if 'backend' in title_lower:
                    allowed_categories.update(['Backend-Framework', 'Enterprise-Lang', 'Database-Query', 'API-REST'])
            else:
                # Non-technical roles (Marketing, Sales, etc.)
                allowed_categories.update(BUSINESS_SET)

            # Link skills, checking for forbidden categories to prevent contamination
            relevant_skills = [s for s in all_skills if s.category in allowed_categories and s.category not in forbidden_categories]
            for skill in relevant_skills:
                db.session.add(RoleSkill(role_id=role.id, skill_id=skill.id))
                added_count += 1

        db.session.commit()
        print(f"[Seeder] Successfully created {added_count} HIERARCHICAL associations across {len(all_roles)} roles.")

if __name__ == '__main__':
    seed_role_skills_hierarchical()
