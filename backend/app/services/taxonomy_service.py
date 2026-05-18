"""
Service for LLM-driven taxonomy discovery and management.
Uses Gemini (google-genai SDK) to extract skills, roles, and sectors from job descriptions,
then creates proper associations between them.
"""
import os
import json
from google import genai
from app import db
from app.models.taxonomy import (
    SkillTaxonomy, RoleTaxonomy, SectorTaxonomy,
    SkillAlias, RoleAlias, SectorAlias, RoleSkill
)
from app.services.data_normalizer import invalidate_cache

_client = None

def _get_client():
    global _client
    if _client is None:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        key = os.getenv('GEMINI_API_KEY', '').replace('"', '').strip()
        if not key:
            raise RuntimeError("No GEMINI_API_KEY set")
        _client = genai.Client(api_key=key)
    return _client


def discover_taxonomy_from_description(title: str, description: str):
    """
    Use Gemini to extract structured taxonomy data from a job description.
    Returns: {skills: [{name, category, aliases}], role: {name, aliases}, sector: {name, aliases}}
    """
    client = _get_client()

    prompt = f"""Analyze the following job listing and extract structured data.

Job Title: {title}
Job Description (first 4000 chars): {description[:4000]}

Extract:
1. **Skills**: Every technical skill, tool, language, framework, methodology, and soft skill mentioned or implied. 
   For each skill provide: canonical_name, category (one of: Language, Framework, Cloud, Database, Tool, DevOps, Domain, Soft), and common aliases.
2. **Role**: The canonical job role title (e.g. "Frontend Developer", "Data Scientist") and alternative titles.
3. **Sector**: The industry sector (e.g. "Engineering", "Data & AI", "Marketing", "Sales", "Design", "Finance & Accounting", "Human Resources", "Operations", "Legal", "Customer Success", "Product Management") and aliases.

Return ONLY a valid JSON object:
{{
  "skills": [
    {{"name": "React", "category": "Framework", "aliases": ["ReactJS", "React.js"]}},
    {{"name": "Python", "category": "Language", "aliases": ["py", "python3"]}}
  ],
  "role": {{"name": "Frontend Developer", "aliases": ["Front-End Engineer", "UI Developer"]}},
  "sector": {{"name": "Engineering", "aliases": ["Software Engineering", "Tech"]}}
}}

Be thorough — extract ALL skills from the description, typically 8-20 skills per job. Include both technical and soft skills.
Do NOT include any markdown formatting or extra text.
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        raw_text = response.text.strip()

        # Clean markdown fences
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        data = json.loads(raw_text.strip())
        return data
    except Exception as e:
        print(f"[TaxonomyDiscovery] LLM Error: {e}")
        return None


def update_taxonomy_with_discovery(data: dict):
    """
    Update the DB taxonomy with data discovered from LLM.
    Creates proper Sector → Role → Skills associations.
    """
    if not data:
        return

    # ── 1. Upsert Sector ──
    sector_obj = None
    sector_data = data.get('sector')
    if sector_data and isinstance(sector_data, dict):
        sector_name = sector_data.get('name', '').strip()
        if sector_name:
            sector_obj = SectorTaxonomy.query.filter(
                db.func.lower(SectorTaxonomy.name) == sector_name.lower()
            ).first()
            if not sector_obj:
                # Check aliases
                alias_hit = SectorAlias.query.filter(
                    db.func.lower(SectorAlias.name) == sector_name.lower()
                ).first()
                if alias_hit:
                    sector_obj = alias_hit.sector
                else:
                    sector_obj = SectorTaxonomy(name=sector_name)
                    db.session.add(sector_obj)
                    db.session.flush()

            # Add aliases
            for a in sector_data.get('aliases', []):
                a_clean = a.strip().lower()
                if a_clean and not SectorAlias.query.filter_by(name=a_clean).first():
                    try:
                        db.session.add(SectorAlias(name=a_clean, sector_id=sector_obj.id))
                        db.session.flush()
                    except Exception:
                        db.session.rollback()

    # ── 2. Upsert Role (linked to sector) ──
    role_obj = None
    role_data = data.get('role')
    if role_data and isinstance(role_data, dict):
        role_name = role_data.get('name', '').strip()
        if role_name:
            role_obj = RoleTaxonomy.query.filter(
                db.func.lower(RoleTaxonomy.title) == role_name.lower()
            ).first()
            if not role_obj:
                # Check aliases
                alias_hit = RoleAlias.query.filter(
                    db.func.lower(RoleAlias.name) == role_name.lower()
                ).first()
                if alias_hit:
                    role_obj = alias_hit.role
                else:
                    role_obj = RoleTaxonomy(
                        title=role_name,
                        sector_id=sector_obj.id if sector_obj else None
                    )
                    db.session.add(role_obj)
                    db.session.flush()
            elif sector_obj and not role_obj.sector_id:
                # Link existing role to sector if missing
                role_obj.sector_id = sector_obj.id

            # Add aliases
            for a in role_data.get('aliases', []):
                a_clean = a.strip().lower()
                if a_clean and not RoleAlias.query.filter_by(name=a_clean).first():
                    try:
                        db.session.add(RoleAlias(name=a_clean, role_id=role_obj.id))
                        db.session.flush()
                    except Exception:
                        db.session.rollback()

    # ── 3. Upsert Skills & Create RoleSkill associations ──
    skills_list = data.get('skills', [])
    for skill_item in skills_list:
        if not isinstance(skill_item, dict):
            continue
        s_name = (skill_item.get('name') or '').strip()
        s_category = (skill_item.get('category') or 'Unknown').strip()
        s_aliases = skill_item.get('aliases', [])
        if not s_name:
            continue

        # Find or create skill
        skill_obj = SkillTaxonomy.query.filter(
            db.func.lower(SkillTaxonomy.canonical_name) == s_name.lower()
        ).first()

        if not skill_obj:
            # Check aliases
            alias_hit = SkillAlias.query.filter(
                db.func.lower(SkillAlias.name) == s_name.lower()
            ).first()
            if alias_hit:
                skill_obj = alias_hit.skill
            else:
                skill_obj = SkillTaxonomy(canonical_name=s_name, category=s_category)
                db.session.add(skill_obj)
                db.session.flush()

        # Add aliases
        for a in s_aliases:
            a_clean = a.strip().lower()
            if a_clean and not SkillAlias.query.filter_by(name=a_clean).first():
                try:
                    db.session.add(SkillAlias(name=a_clean, skill_id=skill_obj.id))
                    db.session.flush()
                except Exception:
                    db.session.rollback()

        # ── Create RoleSkill association ──
        if role_obj and skill_obj:
            existing_link = RoleSkill.query.filter_by(
                role_id=role_obj.id, skill_id=skill_obj.id
            ).first()
            if not existing_link:
                db.session.add(RoleSkill(role_id=role_obj.id, skill_id=skill_obj.id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[TaxonomyService] Commit failed: {e}")
    invalidate_cache()


def clear_all_taxonomy():
    """Clear all taxonomy data."""
    try:
        RoleSkill.query.delete()
        SkillAlias.query.delete()
        RoleAlias.query.delete()
        SectorAlias.query.delete()
        SkillTaxonomy.query.delete()
        RoleTaxonomy.query.delete()
        SectorTaxonomy.query.delete()
        db.session.commit()
        invalidate_cache()
        print("[TaxonomyService] All taxonomy tables cleared.")
    except Exception as e:
        db.session.rollback()
        print(f"[TaxonomyService] Error clearing taxonomy: {e}")
