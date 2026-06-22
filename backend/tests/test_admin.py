"""
Unit tests for administrative taxonomy routes — Sectors, Skills, and Roles.
"""
import pytest
from unittest.mock import patch
from app.models.taxonomy import SectorTaxonomy, SectorAlias, RoleTaxonomy, SkillTaxonomy, RoleSkill
from app.models.user import User

@pytest.fixture
def admin_client(client, session):
    # Pre-create an admin user
    admin = User(email="admin@test.com", google_id="admin_uid", is_admin=True)
    session.add(admin)
    session.commit()
    return client

def _mock_admin_token():
    return patch('firebase_admin.auth.verify_id_token', return_value={'uid': 'admin_uid', 'email': 'admin@test.com', 'name': 'Admin User'})

class TestAdminTaxonomySectors:
    def test_list_sectors(self, admin_client, session):
        s = SectorTaxonomy(name="Software Engineering")
        session.add(s)
        session.commit()

        with _mock_admin_token():
            res = admin_client.get('/api/admin/taxonomy/sectors', headers={'Authorization': 'Bearer mock_token'})
            assert res.status_code == 200
            data = res.get_json()
            assert len(data['sectors']) >= 1
            names = [sec['name'] for sec in data['sectors']]
            assert "Software Engineering" in names

    def test_create_sector(self, admin_client, session):
        with _mock_admin_token():
            res = admin_client.post('/api/admin/taxonomy/sectors', json={'name': 'Healthcare'}, headers={'Authorization': 'Bearer mock_token'})
            assert res.status_code == 201
            sector = session.query(SectorTaxonomy).filter_by(name='Healthcare').first()
            assert sector is not None

    def test_update_sector_rename(self, admin_client, session):
        s = SectorTaxonomy(name="Finance")
        session.add(s)
        session.commit()

        with _mock_admin_token():
            res = admin_client.put(f'/api/admin/taxonomy/sectors/{s.id}', json={'name': 'FinTech', 'aliases': ['banking', 'wealth']}, headers={'Authorization': 'Bearer mock_token'})
            assert res.status_code == 200
            assert s.name == "FinTech"
            aliases = [a.name for a in s.aliases]
            assert "banking" in aliases

    def test_update_sector_merge(self, admin_client, session):
        s1 = SectorTaxonomy(name="Data Science")
        s2 = SectorTaxonomy(name="AI & Analytics")
        session.add_all([s1, s2])
        session.commit()

        # Add a role and skill to s1
        role = RoleTaxonomy(title="Data Scientist", sector_id=s1.id)
        skill = SkillTaxonomy(canonical_name="Pandas", category="Tool", sector_id=s1.id)
        session.add_all([role, skill])
        session.commit()

        with _mock_admin_token():
            # Rename s1 to "AI & Analytics" (s2's name), which triggers merge
            res = admin_client.put(f'/api/admin/taxonomy/sectors/{s1.id}', json={'name': 'AI & Analytics'}, headers={'Authorization': 'Bearer mock_token'})
            assert res.status_code == 200
            data = res.get_json()
            assert data['merged'] is True

            # Check references updated
            assert role.sector_id == s2.id
            assert skill.sector_id == s2.id
            # Check original sector is deleted
            assert session.get(SectorTaxonomy, s1.id) is None
            # Check original name added as alias to target sector
            aliases = [a.name for a in s2.aliases]
            assert "data science" in aliases

    def test_delete_sector(self, admin_client, session):
        s = SectorTaxonomy(name="Unwanted")
        session.add(s)
        session.commit()

        role = RoleTaxonomy(title="Temporary Role", sector_id=s.id)
        session.add(role)
        session.commit()

        with _mock_admin_token():
            res = admin_client.delete(f'/api/admin/taxonomy/sectors/{s.id}', headers={'Authorization': 'Bearer mock_token'})
            assert res.status_code == 200
            assert session.get(SectorTaxonomy, s.id) is None
            assert role.sector_id is None

class TestAdminTaxonomySkillsRoles:
    def test_update_skill_sector(self, admin_client, session):
        s = SectorTaxonomy(name="Creative")
        session.add(s)
        session.commit()

        skill = SkillTaxonomy(canonical_name="Photoshop", category="Tool", sector_id=None)
        session.add(skill)
        session.commit()

        with _mock_admin_token():
            res = admin_client.put(f'/api/admin/taxonomy/skills/{skill.id}', json={'sector_id': s.id}, headers={'Authorization': 'Bearer mock_token'})
            assert res.status_code == 200
            assert skill.sector_id == s.id

    def test_update_role_sector(self, admin_client, session):
        s = SectorTaxonomy(name="Sales")
        session.add(s)
        session.commit()

        role = RoleTaxonomy(title="Account Executive", sector_id=None)
        session.add(role)
        session.commit()

        with _mock_admin_token():
            res = admin_client.put(f'/api/admin/taxonomy/roles/{role.id}', json={'sector_id': s.id}, headers={'Authorization': 'Bearer mock_token'})
            assert res.status_code == 200
            assert role.sector_id == s.id
