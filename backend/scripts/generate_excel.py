import pandas as pd
import os
from app import create_app, db
from app.models.taxonomy import RoleTaxonomy, RoleSkill

def generate():
    app = create_app()
    with app.app_context():
        roles = RoleTaxonomy.query.all()
        data = []
        for r in roles:
            sector_name = r.sector.name if r.sector else 'Unknown'
            r_skills = RoleSkill.query.filter_by(role_id=r.id).all()
            if not r_skills:
                continue 
                
            skill_names = [rs.skill.canonical_name for rs in r_skills if rs.skill]
            skill_str = ', '.join(skill_names)
            
            data.append({
                'Sector': sector_name,
                'Job Role': r.title,
                'Skills': skill_str
            })
            
        df = pd.DataFrame(data)
        df = df.sort_values(by=['Sector', 'Job Role'])
        export_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'taxonomy_report.xlsx'))
        df.to_excel(export_path, index=False)
        print(f'Exported {len(df)} rows to {export_path}')

if __name__ == '__main__':
    generate()
