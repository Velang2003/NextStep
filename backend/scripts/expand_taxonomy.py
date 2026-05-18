from app import create_app, db
from app.models.taxonomy import SectorTaxonomy, RoleTaxonomy, SkillTaxonomy, SectorAlias, RoleAlias, SkillAlias
from app.services.pipeline import _recompute_skill_trends, _recompute_role_trends, _recompute_sector_trends

def expand_taxonomy():
    app = create_app()
    with app.app_context():
        # 1. Expand Sectors
        sectors_data = {
            'Engineering': ['software', 'engineering', 'developer', 'technical'],
            'Data & AI': ['data scientist', 'machine learning', 'ai', 'analytics', 'bi '],
            'Product Management': ['product manager', 'product management', 'program manager'],
            'Design': ['ux', 'ui', 'design', 'creative', 'graphic'],
            'Marketing': ['marketing', 'brand', 'content', 'seo', 'social media', 'growth'],
            'Sales': ['sales', 'account executive', 'business development', 'partnerships'],
            'Human Resources': ['hr', 'recruiting', 'talent', 'people', 'culture', 'human resources'],
            'Operations': ['operations', 'ops', 'logistics', 'strategy', 'planning'],
            'Finance & Accounting': ['finance', 'accounting', 'audit', 'tax', 'treasury', 'cfo'],
            'Legal': ['legal', 'counsel', 'compliance', 'privacy'],
            'Customer Success': ['customer success', 'support', 'customer experience', 'client services']
        }
        
        print("[Expand] Adding sectors...")
        for s_name, aliases in sectors_data.items():
            sector = SectorTaxonomy.query.filter_by(name=s_name).first()
            if not sector:
                sector = SectorTaxonomy(name=s_name)
                db.session.add(sector)
                db.session.flush()
            
            # Add aliases with robust error handling
            for a_name in aliases:
                try:
                    exists = SectorAlias.query.filter_by(name=a_name).first()
                    if not exists:
                        db.session.add(SectorAlias(name=a_name, sector_id=sector.id))
                        db.session.flush()
                except:
                    db.session.rollback()
        
        db.session.commit()

        # 2. Expand Roles
        roles_data = [
            ('Software Engineer', 'Engineering', ['full stack', 'backend', 'frontend', 'sre', 'devops']),
            ('Data Scientist', 'Data & AI', ['data analyst', 'ml engineer', 'ai researcher']),
            ('Product Manager', 'Product Management', ['pm', 'associate pm', 'senior pm']),
            ('UX Researcher', 'Design', ['user researcher', 'product designer']),
            ('Marketing Manager', 'Marketing', ['growth marketer', 'content strategist']),
            ('Account Executive', 'Sales', ['sales rep', 'bd manager']),
            ('HR Generalist', 'Human Resources', [' People person', 'Recruiter']),
            ('Business Analyst', 'Operations', ['strategy analyst', 'ops manager']),
            ('Financial Analyst', 'Finance & Accounting', ['fp&a', 'controller']),
            ('Legal Counsel', 'Legal', ['attorney', 'legal associate']),
            ('Customer Success Manager', 'Customer Success', ['csm', 'support lead'])
        ]
        
        print("[Expand] Adding roles...")
        for title, s_name, aliases in roles_data:
            sector = SectorTaxonomy.query.filter_by(name=s_name).first()
            role = RoleTaxonomy.query.filter_by(title=title).first()
            if not role:
                role = RoleTaxonomy(title=title, sector_id=sector.id if sector else None)
                db.session.add(role)
                db.session.flush()
            
            for a_name in aliases:
                try:
                    exists = RoleAlias.query.filter_by(name=a_name).first()
                    if not exists:
                        db.session.add(RoleAlias(name=a_name, role_id=role.id))
                        db.session.flush()
                except:
                    db.session.rollback()
        
        db.session.commit()

        # 3. Expand Skills
        skills_data = [
            ('Python', 'Language', ['py', 'scripting', 'python3']),
            ('JavaScript', 'Language', ['js', 'node', 'javascript', 'es6']),
            ('TypeScript', 'Language', ['ts', 'typescript']),
            ('Go', 'Language', ['golang']),
            ('React', 'Framework', ['frontend', 'ui', 'react.js', 'reactjs']),
            ('Angular', 'Framework', ['angularjs', 'angular', 'frontend']),
            ('Vue', 'Framework', ['vuejs', 'vue.js', 'frontend']),
            ('Docker', 'Tool', ['container', 'containerization']),
            ('Kubernetes', 'Tool', ['k8s', 'container orchestration']),
            ('GraphQL', 'API', ['graphql query', 'gql']),
            ('Tailwind CSS', 'Framework', ['tailwind', 'css framework']),
            ('SQL', 'Database', ['mysql', 'postgres', 'sql server', 'postgresql']),
            ('NoSQL', 'Database', ['mongodb', 'cassandra', 'dynamodb']),
            ('AWS', 'Cloud', ['cloud', 'infrastructure', 'amazon web services']),
            ('Azure', 'Cloud', ['microsoft azure', 'cloud']),
            ('GCP', 'Cloud', ['google cloud platform', 'google cloud']),
            ('Excel', 'Tool', ['spreadsheets', 'vlookup', 'microsoft excel']),
            ('Figma', 'Tool', ['design', 'prototyping', 'ui/ux']),
            ('Salesforce', 'Tool', ['crm', 'sales ops']),
            ('Project Management', 'Domain', ['agile', 'scrum', 'kanban']),
            ('Strategy', 'Domain', ['planning', 'analysis', 'strategic planning']),
            ('Communication', 'Soft', ['writing', 'presentation', 'verbal communication']),
            ('Machine Learning', 'Domain', ['ml', 'deep learning', 'neural networks']),
            ('Data Analysis', 'Domain', ['analytics', 'data modeling']),
            ('CI/CD', 'Tool', ['continuous integration', 'continuous deployment', 'jenkins', 'github actions'])
        ]
        
        print("[Expand] Adding skills...")
        for s_name, cat, aliases in skills_data:
            skill = SkillTaxonomy.query.filter_by(canonical_name=s_name).first()
            if not skill:
                skill = SkillTaxonomy(canonical_name=s_name, category=cat)
                db.session.add(skill)
                db.session.flush()
            
            for a_name in aliases:
                try:
                    exists = SkillAlias.query.filter_by(name=a_name).first()
                    if not exists:
                        db.session.add(SkillAlias(name=a_name, skill_id=skill.id))
                        db.session.flush()
                except:
                    db.session.rollback()
        
        db.session.commit()

        # 4. Map proper associations manually to bypass Gemini 503 outage
        print("[Expand] Creating Role-Skill Associations...")
        from app.models.taxonomy import RoleSkill
        role_skill_map = {
            'Software Engineer': ['Python', 'JavaScript', 'TypeScript', 'Go', 'React', 'Docker', 'SQL', 'AWS', 'CI/CD'],
            'Data Scientist': ['Python', 'SQL', 'AWS', 'Machine Learning', 'Data Analysis'],
            'Product Manager': ['Strategy', 'Project Management', 'Communication', 'Data Analysis'],
            'UX Researcher': ['Figma', 'Strategy', 'Communication'],
            'Marketing Manager': ['Excel', 'Communication', 'Strategy'],
            'Account Executive': ['Salesforce', 'Communication', 'Strategy'],
            'HR Generalist': ['Communication', 'Strategy'],
            'Business Analyst': ['Excel', 'SQL', 'Data Analysis', 'Strategy'],
            'Financial Analyst': ['Excel', 'Data Analysis', 'Strategy'],
            'Customer Success Manager': ['Salesforce', 'Communication']
        }
        
        for role_title, skills in role_skill_map.items():
            role = RoleTaxonomy.query.filter_by(title=role_title).first()
            if not role: continue
            for skill_name in skills:
                skill = SkillTaxonomy.query.filter_by(canonical_name=skill_name).first()
                if not skill: continue
                # create link
                if not RoleSkill.query.filter_by(role_id=role.id, skill_id=skill.id).first():
                    db.session.add(RoleSkill(role_id=role.id, skill_id=skill.id))
        db.session.commit()

        print("[Expand] Taxonomy expanded successfully. Recomputing trends...")
        from app.models.job import JobListing
        from app.services.data_normalizer import classify_department, extract_skills, normalize_role, invalidate_cache
        
        invalidate_cache()
        
        jobs = JobListing.query.all()
        for idx, job in enumerate(jobs):
            job.department = job.department or ''
            job.sector = classify_department(job.title, job.department)
            if idx % 500 == 0:
                print(f"[Expand] Reclassified {idx} jobs...")
        
        db.session.commit()
        
        print("[Expand] Recomputing trends in DB...")
        _recompute_sector_trends()
        _recompute_role_trends()
        all_jobs_dicts = [j.to_dict() for j in JobListing.query.all()]
        _recompute_skill_trends(all_jobs_dicts)
        
        print("[Expand] Finished logic update.")

if __name__ == "__main__":
    expand_taxonomy()
