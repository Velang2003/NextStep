"""
seed_aliases.py
===============
Seeds UNIQUE, role-specific aliases for all roles and skills in the taxonomy.

Design Rule: An alias must be specific enough that it ONLY maps to one role
or one skill. Generic terms like 'developer', 'engineer', 'analyst' are NOT
valid aliases because they would match multiple entries — causing wrong
learning path recommendations.

Good alias examples:
  - "Frontend Developer" → alias: "front end developer", "frontend dev", "fe developer"
  - "Backend Developer"  → alias: "back end developer", "backend dev", "server-side developer"
  - NOT: "developer" (matches both)

Run: python seed_aliases.py
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.taxonomy import (
    RoleTaxonomy, RoleAlias,
    SkillTaxonomy, SkillAlias,
)


# ─────────────────────────────────────────────────────────────────────────────
# ROLE ALIASES — specific multi-word phrases only
# Each alias MUST uniquely identify exactly one role. Single generic words
# like "developer", "engineer", "analyst" are intentionally excluded.
# ─────────────────────────────────────────────────────────────────────────────
ROLE_ALIAS_MAP = {
    ".NET Developer":                 ["dotnet developer", "dot net developer", ".net software developer", "asp.net developer", "c# .net developer"],
    "2D Artist/Animator":             ["2d animator", "two-d animator", "2d character animator", "2d motion artist"],
    "3D Artist/Animator":             ["3d animator", "three-d animator", "3d character artist", "3d motion designer"],
    "Accessibility Specialist":       ["a11y specialist", "accessibility engineer", "wcag specialist", "web accessibility engineer"],
    "Admin Big Data":                 ["big data administrator", "big data admin", "hdfs administrator", "hadoop admin"],
    "Agile Project Manager":          ["agile pm", "agile project lead", "scrum project manager", "agile delivery manager"],
    "Android Developer":              ["android app developer", "android mobile developer", "android software engineer", "kotlin android developer"],
    "Animator":                       ["motion graphics animator", "vfx animator", "character animator", "animation artist"],
    "Ansible Automation Engineer":    ["ansible engineer", "ansible devops engineer", "ansible automation specialist"],
    "Ansible Operations Engineer":    ["ansible ops engineer", "ansible operations specialist", "ansible sre"],
    "API Developer":                  ["api software developer", "rest api developer", "api integration developer", "web api developer"],
    "Application Designer":           ["application ux designer", "app interface designer", "software application designer"],
    "Application Engineer":           ["application software engineer", "enterprise application engineer", "app support engineer"],
    "Application Security Engineer":  ["appsec engineer", "application security specialist", "secure sdlc engineer", "sast/dast engineer"],
    "Art Director":                   ["creative art director", "visual art director", "design art director"],
    "Artificial Intelligence Researcher": ["ai researcher", "ml researcher", "deep learning researcher", "ai scientist"],
    "Big Data Architect":             ["big data solution architect", "hadoop architect", "data lake architect", "spark architect"],
    "Big Data Engineer":              ["big data pipeline engineer", "hadoop engineer", "spark data engineer", "hdfs engineer"],
    "Big Data Specialist":            ["big data consultant", "big data analyst specialist", "large scale data specialist"],
    "Business Intelligence Analyst":  ["bi analyst", "business intelligence reporting analyst", "power bi analyst", "tableau analyst"],
    "Business Intelligence Developer":["bi developer", "business intelligence software developer", "tableau developer", "power bi developer"],
    "C# Developer":                   ["csharp developer", "c sharp developer", "c# software engineer", "dotnet c# developer"],
    "Chef InSpec Engineer":           ["chef inspec specialist", "inspec compliance engineer"],
    "Chef Operations Engineer":       ["chef ops engineer", "chef configuration management engineer"],
    "Chief Information Officer":      ["cio", "chief it officer", "head of information technology"],
    "Chief Technology Officer":       ["cto", "chief tech officer", "head of technology", "vp of engineering and technology"],
    "Coder":                          ["software coder", "entry level coder", "programming coder"],
    "Computer Forensic Analyst":      ["digital forensics analyst", "cyber forensic analyst", "forensic computer investigator"],
    "Computer Programmer":            ["software programmer", "application programmer", "computer software programmer"],
    "Consul Engineer":                ["hashicorp consul engineer", "service mesh consul engineer"],
    "Cybersecurity Analyst":          ["cyber security analyst", "information security analyst", "soc analyst", "threat analyst"],
    "Cybersecurity Engineer":         ["cyber security engineer", "information security engineer", "network security engineer ii"],
    "Cybersecurity Specialist":       ["cyber security specialist", "infosec specialist", "cybersecurity consultant"],
    "Data Analyst":                   ["data analysis specialist", "data reporting analyst", "sql data analyst", "business data analyst"],
    "Data Architect":                 ["data solutions architect", "enterprise data architect", "cloud data architect"],
    "Data Engineer":                  ["data pipeline engineer", "etl developer", "data infrastructure engineer", "dataops engineer"],
    "Data Modeler":                   ["data modeling engineer", "database modeler", "erwin data modeler", "logical data modeler"],
    "Data Scientist":                 ["applied data scientist", "ml data scientist", "research data scientist", "predictive analytics scientist"],
    "Developer":                      ["general software developer", "junior coder developer"],
    "Director of Engineering":        ["vp engineering", "engineering director", "head of software engineering"],
    "Docker Engineer":                ["docker container engineer", "docker devops engineer", "containerization engineer"],
    "E-Commerce Developer":           ["ecommerce developer", "e-commerce software developer", "shopify developer", "magento developer", "woocommerce developer"],
    "Embedded Software Engineer":     ["embedded systems engineer", "firmware engineer", "embedded c developer", "rtos engineer"],
    "Entry Level Developer":          ["junior software developer", "graduate developer", "associate developer", "trainee developer"],
    "Envoy Engineer":                 ["envoy proxy engineer", "service proxy engineer"],
    "Falco Engineer":                 ["falco security engineer", "runtime security engineer"],
    "FluentD Engineer":               ["fluentd log engineer", "log aggregation engineer"],
    "Full Stack Developer":           ["full stack software developer", "fullstack developer", "full-stack engineer", "full stack web developer"],
    "Full Stack JAVA Developer":      ["java fullstack developer", "full stack java engineer", "java full-stack developer", "spring boot fullstack developer"],
    "Full Stack Python Developer":    ["python fullstack developer", "full stack python engineer", "django fullstack developer", "flask fullstack developer"],
    "Game Developer":                 ["video game developer", "unity game developer", "unreal engine developer", "game software engineer"],
    "Information Security Analyst":   ["infosec analyst", "iso 27001 analyst", "security operations analyst"],
    "Interaction Designer":           ["ixd designer", "interactive designer", "human computer interaction designer"],
    "IOS Developer":                  ["ios app developer", "iphone developer", "swift ios developer", "objective-c ios developer", "apple ios developer"],
    "Istio Engineer":                 ["istio service mesh engineer", "kubernetes istio engineer"],
    "IT Director":                    ["director of it", "it operations director", "head of it"],
    "IT Manager":                     ["it operations manager", "information technology manager", "it infrastructure manager"],
    "IT Security Specialist":         ["it security analyst", "endpoint security specialist", "it cybersecurity specialist"],
    "Junior Developer":               ["junior software engineer", "entry-level developer", "associate software developer"],
    "Kubernetes Administrator":       ["k8s administrator", "kubernetes cluster admin", "kubernetes devops admin"],
    "Kubernetes Engineer":            ["k8s engineer", "kubernetes platform engineer", "container orchestration engineer"],
    "Machine Learning Engineer":      ["ml engineer", "machine learning developer", "mlops engineer", "ai/ml engineer"],
    "Mainframe Developer":            ["ibm mainframe developer", "cobol developer", "zos developer", "mainframe software engineer"],
    "Mobile App Developer":           ["mobile application developer", "cross-platform mobile developer", "react native developer", "flutter developer"],
    "Network Security Engineer":      ["network infosec engineer", "firewall engineer", "network security architect"],
    "Nomad Engineer":                 ["hashicorp nomad engineer", "job scheduler engineer"],
    "OpenShift Engineer":             ["red hat openshift engineer", "openshift container platform engineer"],
    "Packer Engineer":                ["hashicorp packer engineer", "image build automation engineer"],
    "Penetration Tester":             ["pen tester", "ethical hacker", "penetration testing specialist", "offensive security engineer"],
    "PHP Developer":                  ["php software developer", "laravel developer", "symfony developer", "php web developer"],
    "Product Manager":                ["product management specialist", "digital product manager", "software product manager", "technical product manager"],
    "Program Manager":                ["technical program manager", "engineering program manager", "it program manager"],
    "Project Manager":                ["it project manager", "software project manager", "technical project manager", "pmo manager"],
    "Puppet Operations Engineer":     ["puppet devops engineer", "puppet automation engineer"],
    "Python Developer":               ["python software developer", "python backend developer", "django developer", "flask developer"],
    "Security Administrator":         ["security systems administrator", "it security administrator", "cybersecurity administrator"],
    "Sharepoint Developer":           ["microsoft sharepoint developer", "sharepoint online developer", "sharepoint .net developer"],
    "Software Developer":             ["software development engineer", "software application developer", "professional software developer"],
    "Software Engineer":              ["software development engineer ii", "sde", "software engineering specialist", "sr software engineer"],
    "Technical Lead":                 ["tech lead", "engineering lead", "software technical lead", "lead software engineer"],
    "Terraform Engineer":             ["hashicorp terraform engineer", "infrastructure as code engineer", "terraform devops engineer"],
    "UI Designer":                    ["user interface designer", "ui graphic designer", "visual ui designer"],
    "UI Developer":                   ["user interface developer", "frontend ui developer", "ui web developer"],
    "UX Designer":                    ["user experience designer", "ux research designer", "product ux designer"],
    "UX/UI Designer":                 ["ux ui designer", "user experience and interface designer", "product designer ux ui"],
    "Vault Engineer":                 ["hashicorp vault engineer", "secrets management engineer"],
    "Web Developer":                  ["website developer", "web application developer", "web software developer"],
}


# ─────────────────────────────────────────────────────────────────────────────
# SKILL ALIASES — specific, non-ambiguous aliases only
# ─────────────────────────────────────────────────────────────────────────────
SKILL_ALIAS_MAP = {
    # Languages
    "Python":           ["python3", "python 3", "py", "python programming"],
    "JavaScript":       ["js", "javascript es6", "ecmascript", "vanilla javascript", "vanilla js"],
    "TypeScript":       ["ts", "typescript js", "typed javascript"],
    "Java":             ["java se", "java ee", "java 17", "core java", "java programming"],
    "C#":               ["csharp", "c sharp", "dotnet c#"],
    "C++":              ["cpp", "c plus plus"],
    "Go":               ["golang", "go lang", "go programming language"],
    "Rust":             ["rust lang", "rust programming"],
    "PHP":              ["php 8", "php7", "hypertext preprocessor"],
    "Ruby":             ["ruby lang", "ruby programming"],
    "Swift":            ["swift ios", "apple swift", "swift 5"],
    "Kotlin":           ["kotlin android", "kotlin jvm"],
    "Scala":            ["scala lang", "scala jvm", "apache spark scala"],
    "R":                ["r language", "r programming", "rlang"],

    # Frontend
    "React":            ["reactjs", "react.js", "react framework", "react library"],
    "Angular":          ["angularjs", "angular 2+", "angular framework"],
    "Vue.js":           ["vuejs", "vue js", "vue framework"],
    "Next.js":          ["nextjs", "next js", "next.js framework"],
    "HTML":             ["html5", "hypertext markup language"],
    "CSS":              ["css3", "cascading style sheets"],
    "Sass":             ["scss", "sass css", "sass preprocessor"],
    "Tailwind CSS":     ["tailwindcss", "tailwind", "utility-first css"],
    "Bootstrap":        ["bootstrap css", "twitter bootstrap", "bootstrap 5"],

    # Backend / Frameworks
    "Node.js":          ["nodejs", "node js", "express node"],
    "Express.js":       ["expressjs", "express node.js", "express framework"],
    "Django":           ["django python", "django framework", "django rest framework", "drf"],
    "Flask":            ["flask python", "flask microframework", "flask api"],
    "Spring Boot":      ["spring framework", "java spring boot", "spring mvc"],
    "FastAPI":          ["fastapi python", "python fastapi"],
    "Laravel":          ["laravel php", "php laravel framework"],

    # Databases
    "SQL":              ["structured query language", "sql queries", "sql database"],
    "MySQL":            ["mysql db", "mysql database", "mysql server"],
    "PostgreSQL":       ["postgres", "postgresql db", "pgsql"],
    "MongoDB":          ["mongo", "mongodb database", "nosql mongodb"],
    "Redis":            ["redis cache", "redis db", "redis queue"],
    "Elasticsearch":    ["elastic search", "elk elasticsearch", "opensearch"],
    "SQLite":           ["sqlite3", "sqlite database"],
    "Oracle DB":        ["oracle database", "oracle sql", "pl/sql"],

    # Cloud
    "AWS":              ["amazon web services", "aws cloud", "amazon aws"],
    "Azure":            ["microsoft azure", "azure cloud", "ms azure"],
    "GCP":              ["google cloud platform", "google cloud", "gcp cloud"],
    "Firebase":         ["google firebase", "firebase realtime", "firebase sdk"],

    # DevOps / Infrastructure
    "Docker":           ["docker container", "docker compose", "dockerfile"],
    "Kubernetes":       ["k8s", "kubernetes cluster", "kubectl"],
    "Terraform":        ["terraform iac", "hashicorp terraform", "terraform cloud"],
    "CI/CD":            ["continuous integration", "continuous deployment", "cicd pipeline"],
    "Jenkins":          ["jenkins ci", "jenkins pipeline", "jenkins server"],
    "GitHub Actions":   ["github ci", "gha", "github workflows"],
    "Ansible":          ["ansible automation", "ansible playbook", "ansible tower"],
    "Linux":            ["linux os", "ubuntu server", "centos", "rhel"],
    "Nginx":            ["nginx server", "nginx proxy", "nginx web server"],

    # Data / ML
    "Machine Learning": ["ml", "machine learning algorithms", "supervised learning", "ml models"],
    "Deep Learning":    ["dl", "neural networks", "deep neural network", "cnn rnn"],
    "TensorFlow":       ["tensorflow 2", "tf2", "tensorflow framework"],
    "PyTorch":          ["pytorch framework", "torch python"],
    "Pandas":           ["pandas python", "pandas dataframe", "python pandas"],
    "NumPy":            ["numpy python", "python numpy"],
    "Scikit-learn":     ["sklearn", "scikit learn", "python sklearn"],
    "Apache Spark":     ["spark", "pyspark", "spark streaming"],
    "Apache Kafka":     ["kafka", "kafka streaming", "kafka broker"],

    # Tools
    "Git":              ["git version control", "git scm", "source control git"],
    "JIRA":             ["jira project management", "atlassian jira", "jira software"],
    "Figma":            ["figma design", "figma ui", "figma prototyping"],
    "Adobe XD":         ["xd design", "adobe xd prototyping"],
    "Postman":          ["postman api", "postman testing", "api testing postman"],
    "Swagger":          ["swagger api", "openapi swagger", "swagger docs"],
    "GraphQL":          ["graphql api", "graphql schema", "apollo graphql"],
    "REST API":         ["restful api", "rest web service", "http rest api"],
    "Salesforce":       ["sfdc", "salesforce crm", "salesforce platform"],
    "Excel":            ["microsoft excel", "ms excel", "excel spreadsheet"],

    # Soft Skills
    "Communication":    ["verbal communication", "written communication", "effective communication"],
    "Strategy":         ["strategic planning", "business strategy", "strategic thinking"],
    "Leadership":       ["team leadership", "people management", "lead teams"],
    "Agile":            ["agile methodology", "agile scrum", "agile development"],
    "Scrum":            ["scrum methodology", "scrum master", "scrum framework"],
    "Project Management": ["pm skills", "project planning", "project delivery"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def seed_aliases():
    app = create_app()
    with app.app_context():
        role_hits = role_miss = 0
        skill_hits = skill_miss = 0
        alias_added = 0
        conflicts = 0

        print("=" * 60)
        print("SEEDING ROLE ALIASES")
        print("=" * 60)

        for role_title, aliases in ROLE_ALIAS_MAP.items():
            role = RoleTaxonomy.query.filter(
                db.func.lower(RoleTaxonomy.title) == role_title.lower()
            ).first()
            if not role:
                print(f"  [MISS] Role not found: {role_title}")
                role_miss += 1
                continue
            role_hits += 1

            for alias_name in aliases:
                alias_clean = alias_name.strip().lower()
                if not alias_clean:
                    continue
                # Check for cross-role conflicts
                existing = RoleAlias.query.filter_by(name=alias_clean).first()
                if existing and existing.role_id != role.id:
                    print(f"  [CONFLICT] '{alias_clean}' already belongs to '{existing.role.title}' — skipping for '{role_title}'")
                    conflicts += 1
                    continue
                if not existing:
                    db.session.add(RoleAlias(name=alias_clean, role_id=role.id))
                    alias_added += 1

        db.session.commit()
        print(f"\nRoles: {role_hits} matched, {role_miss} not found")

        print("\n" + "=" * 60)
        print("SEEDING SKILL ALIASES")
        print("=" * 60)

        for skill_name, aliases in SKILL_ALIAS_MAP.items():
            skill = SkillTaxonomy.query.filter(
                db.func.lower(SkillTaxonomy.canonical_name) == skill_name.lower()
            ).first()
            if not skill:
                print(f"  [MISS] Skill not found: {skill_name}")
                skill_miss += 1
                continue
            skill_hits += 1

            for alias_name in aliases:
                alias_clean = alias_name.strip().lower()
                if not alias_clean:
                    continue
                # Check for cross-skill conflicts
                existing = SkillAlias.query.filter_by(name=alias_clean).first()
                if existing and existing.skill_id != skill.id:
                    print(f"  [CONFLICT] '{alias_clean}' already aliases '{existing.skill.canonical_name}' — skipping for '{skill_name}'")
                    conflicts += 1
                    continue
                if not existing:
                    db.session.add(SkillAlias(name=alias_clean, skill_id=skill.id))
                    alias_added += 1

        db.session.commit()
        print(f"\nSkills: {skill_hits} matched, {skill_miss} not found")

        print("\n" + "=" * 60)
        print(f"DONE: {alias_added} aliases added, {conflicts} conflicts skipped")
        print("=" * 60)

        # Final counts
        print(f"\nDB Summary:")
        print(f"  RoleAlias total:  {RoleAlias.query.count()}")
        print(f"  SkillAlias total: {SkillAlias.query.count()}")


if __name__ == '__main__':
    seed_aliases()
