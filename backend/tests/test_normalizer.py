import pytest
from app.services.data_normalizer import extract_skills, classify_department, normalize_role, invalidate_cache
from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, RoleTaxonomy, SkillAlias, RoleAlias, SectorAlias

@pytest.fixture
def seed_taxonomy(session):
    # Seed Skills
    python = SkillTaxonomy(canonical_name="Python", category="Language")
    react = SkillTaxonomy(canonical_name="React", category="Framework")
    session.add_all([python, react])
    session.flush()
    session.add(SkillAlias(name="py", skill_id=python.id))
    session.add(SkillAlias(name="reactjs", skill_id=react.id))
    
    # Seed Sectors
    eng = SectorTaxonomy(name="Engineering")
    session.add(eng)
    session.flush()
    session.add(SectorAlias(name="software", sector_id=eng.id))
    
    # Seed Roles
    swe = RoleTaxonomy(title="Software Engineer", sector_id=eng.id)
    session.add(swe)
    session.flush()
    session.add(RoleAlias(name="swe", role_id=swe.id))
    session.add(RoleAlias(name="developer", role_id=swe.id))
    
    session.commit()
    invalidate_cache()

def test_extract_skills(seed_taxonomy):
    text = "Looking for a Python developer with experience in ReactJS and Py."
    skills = extract_skills(text)
    assert "Python" in skills
    assert "React" in skills
    assert len(skills) == 2

def test_classify_department(seed_taxonomy):
    assert classify_department("Software Developer", "Engineering") == "Engineering"
    assert classify_department("Marketing Manager", "Sales") == "Other"

def test_normalize_role(seed_taxonomy):
    assert normalize_role("Senior SWE") == "Software Engineer"
    assert normalize_role("Backend Developer") == "Software Engineer"
