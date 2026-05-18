"""
Seed the taxonomy tables from data/taxonomy_data.json.
Run: python seed_taxonomy.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, RoleTaxonomy, CountryMapping, SkillAlias, SectorAlias, RoleAlias

DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'taxonomy_data.json'))


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # --- Skills ---
        existing_skills = {s.canonical_name for s in SkillTaxonomy.query.all()}
        seen_skill_aliases = set()
        added_skills = 0
        for skill in data.get('skills', []):
            if skill['name'] not in existing_skills:
                clean_aliases = []
                for a in skill.get('aliases', []):
                    a_lower = a.lower().strip()
                    if a_lower not in seen_skill_aliases:
                        seen_skill_aliases.add(a_lower)
                        clean_aliases.append(SkillAlias(name=a_lower))

                db.session.add(SkillTaxonomy(
                    canonical_name=skill['name'],
                    category=skill['category'],
                    aliases=clean_aliases
                ))
                added_skills += 1
        print(f"[Seed] Skills: {added_skills} added, {len(existing_skills)} already existed")

        # --- Sectors ---
        existing_sectors = {s.name for s in SectorTaxonomy.query.all()}
        seen_sector_aliases = set()
        sector_map = {}
        added_sectors = 0
        for sector in data.get('sectors', []):
            if sector['name'] not in existing_sectors:
                clean_aliases = []
                for a in sector.get('keywords', []):
                    a_lower = a.lower().strip()
                    if a_lower not in seen_sector_aliases:
                        seen_sector_aliases.add(a_lower)
                        clean_aliases.append(SectorAlias(name=a_lower))

                s = SectorTaxonomy(
                    name=sector['name'],
                    aliases=clean_aliases
                )
                db.session.add(s)
                db.session.flush()
                sector_map[sector['name']] = s.id
                added_sectors += 1
            else:
                s = SectorTaxonomy.query.filter_by(name=sector['name']).first()
                sector_map[sector['name']] = s.id
        print(f"[Seed] Sectors: {added_sectors} added, {len(existing_sectors)} already existed")

        # --- Roles ---
        existing_roles = {r.title for r in RoleTaxonomy.query.all()}
        seen_role_aliases = set()
        added_roles = 0
        for role in data.get('roles', []):
            if role['title'] not in existing_roles:
                clean_aliases = []
                for a in role.get('keywords', []):
                    a_lower = a.lower().strip()
                    if a_lower not in seen_role_aliases:
                        seen_role_aliases.add(a_lower)
                        clean_aliases.append(RoleAlias(name=a_lower))

                db.session.add(RoleTaxonomy(
                    title=role['title'],
                    sector_id=sector_map.get(role.get('sector')),
                    seniority=role.get('seniority'),
                    aliases=clean_aliases
                ))
                added_roles += 1
        print(f"[Seed] Roles: {added_roles} added, {len(existing_roles)} already existed")

        # --- Countries ---
        existing_countries = {c.iso3 for c in CountryMapping.query.all()}
        added_countries = 0
        for country in data.get('countries', []):
            if country['iso3'] not in existing_countries:
                db.session.add(CountryMapping(
                    country_name=country['name'],
                    iso3=country['iso3'],
                    iso2=country['iso2'],
                    aliases=country.get('aliases', []),
                    lat=country.get('lat'),
                    lng=country.get('lng'),
                ))
                added_countries += 1
        print(f"[Seed] Countries: {added_countries} added, {len(existing_countries)} already existed")

        db.session.commit()
        print("[Seed] Done!")


if __name__ == '__main__':
    seed()
