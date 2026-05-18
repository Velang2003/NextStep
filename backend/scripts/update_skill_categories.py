import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.taxonomy import SkillTaxonomy

def update_skill_categories():
    app = create_app()
    with app.app_context():
        print("[Patcher] Updating Skill Categories for High-Resolution Taxonomy...")
        
        mappings = {
            # Languages
            'JavaScript': 'Web-Lang',
            'TypeScript': 'Web-Lang',
            'PHP': 'Web-Lang',
            'Solidity': 'Web-Lang',
            'Dart': 'Web-Lang',
            'Python': 'Data-Lang',
            'R': 'Data-Lang',
            'MATLAB': 'Data-Lang',
            'Scala': 'Data-Lang',
            'Go': 'System-Lang',
            'Rust': 'System-Lang',
            'C++': 'System-Lang',
            'C': 'System-Lang',
            'Elixir': 'System-Lang',
            'Lua': 'System-Lang',
            'Perl': 'System-Lang',
            'Shell Scripting': 'System-Lang',
            'PowerShell': 'System-Lang',
            'Java': 'Enterprise-Lang',
            'C#': 'Enterprise-Lang',
            'Ruby': 'Enterprise-Lang',
            'Kotlin': 'App-Lang',
            'Swift': 'App-Lang',
            
            # Frameworks
            'React': 'Frontend-Framework',
            'Vue.js': 'Frontend-Framework',
            'Angular': 'Frontend-Framework',
            'Next.js': 'Frontend-Framework',
            'Svelte': 'Frontend-Framework',
            'Tailwind CSS': 'Frontend-Framework',
            'HTML/CSS': 'Frontend-Framework',
            'Node.js': 'Backend-Framework',
            'Flask': 'Backend-Framework',
            'Django': 'Backend-Framework',
            'FastAPI': 'Backend-Framework',
            'Spring Boot': 'Backend-Framework',
            'Express.js': 'Backend-Framework',
            'Ruby on Rails': 'Backend-Framework',
            'ASP.NET': 'Backend-Framework',
            
            # Others
            'SQL': 'Database-Query',
            'NoSQL': 'Database-Doc',
            'Redis': 'Database-Cache',
            'REST API': 'API-REST',
            'GraphQL': 'API-Graph',
            'gRPC': 'API-RPC'
        }
        
        updated_count = 0
        for name, new_cat in mappings.items():
            skill = SkillTaxonomy.query.filter_by(canonical_name=name).first()
            if skill:
                skill.category = new_cat
                updated_count += 1
        
        db.session.commit()
        print(f"[Patcher] Successfully updated {updated_count} skills with granular categories.")

if __name__ == '__main__':
    update_skill_categories()
