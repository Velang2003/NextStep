"""
seed_from_excel.py
==================
Wipes existing taxonomy data (roles, skills, sectors + their aliases)
and re-seeds from 'JOB Data.xlsx' located in the backend folder.

Strategy
--------
* One sector: IT
* Roles  -> unique Job Titles from column 1, all linked to IT sector
* Skills -> all unique skill tokens extracted from column 2, no aliases
* role_skill -> many-to-many linking each role to its skills

Run:
    venv\\Scripts\\python.exe seed_from_excel.py
"""

import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import openpyxl
from app import create_app, db
from app.models.taxonomy import (
    SkillTaxonomy, SkillAlias,
    SectorTaxonomy, SectorAlias,
    RoleTaxonomy, RoleAlias,
    RoleSkill,
)

EXCEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'JOB Data.xlsx'))
IT_SECTOR_NAME = 'IT'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_skills(raw: str) -> list[str]:
    """Split a comma-separated skills string into a clean list."""
    if not raw:
        return []
    return [s.strip() for s in raw.split(',') if s.strip()]


def load_excel() -> list[dict]:
    """Return rows as list of dicts with keys 'title' and 'skills'."""
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active

    rows = []
    header_skipped = False
    for row in ws.iter_rows(values_only=True):
        if not header_skipped:
            header_skipped = True   # skip header row
            continue
        job_title, skills_raw = row[0], row[1]
        if not job_title:
            continue
        rows.append({
            'title': str(job_title).strip(),
            'skills': parse_skills(str(skills_raw) if skills_raw else ''),
        })

    print(f"[Excel] Loaded {len(rows)} job rows from '{EXCEL_PATH}'")
    return rows


# ---------------------------------------------------------------------------
# Wipe helpers
# ---------------------------------------------------------------------------

def wipe_taxonomy_tables():
    """
    Truncate all taxonomy tables using raw SQL.
    FOREIGN_KEY_CHECKS is temporarily disabled so MySQL allows truncation
    even when other tables (assessments, etc.) reference taxonomy rows.
    The order still respects FK structure for safety, but the checks bypass
    ensures we aren't blocked by referencing tables outside taxonomy scope.
    """
    tables = [
        'role_skill',
        'role_alias',
        'skill_alias',
        'sector_alias',
        'role_taxonomy',
        'skill_taxonomy',
        'sector_taxonomy',
    ]
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in tables:
            result = conn.execute(db.text(f"DELETE FROM `{table}`"))
            print(f"[Wipe] {table}: {result.rowcount} rows deleted")
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        trans.commit()
    except Exception:
        trans.rollback()
        conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # ── 1. Wipe ──────────────────────────────────────────────────────
        print("\n=== Wiping existing taxonomy tables ===")
        wipe_taxonomy_tables()

        # ── 2. Load Excel ────────────────────────────────────────────────
        print("\n=== Loading data from Excel ===")
        job_rows = load_excel()

        # ── 3. Seed IT sector (single sector, no aliases) ────────────────
        print("\n=== Seeding sector ===")
        it_sector = SectorTaxonomy(name=IT_SECTOR_NAME)
        db.session.add(it_sector)
        db.session.flush()          # get it_sector.id immediately
        print(f"[Seed] Sector '{IT_SECTOR_NAME}' created (id={it_sector.id})")

        # ── 4. Collect all unique skills ─────────────────────────────────
        print("\n=== Collecting unique skills ===")
        all_skill_names: set[str] = set()
        for row in job_rows:
            for skill in row['skills']:
                all_skill_names.add(skill)   # preserve original casing

        skill_map: dict[str, int] = {}       # canonical_name -> skill.id
        for skill_name in sorted(all_skill_names):
            st = SkillTaxonomy(
                canonical_name=skill_name,
                category='IT',               # broad category; refine later
                is_approved=True,
            )
            db.session.add(st)
            db.session.flush()
            skill_map[skill_name] = st.id

        print(f"[Seed] Skills inserted: {len(skill_map)}")

        # ── 5. Seed roles + role_skill links ─────────────────────────────
        print("\n=== Seeding roles and role-skill links ===")
        seen_titles: set[str] = set()
        roles_added = 0
        role_skills_added = 0

        for row in job_rows:
            title = row['title']
            if title in seen_titles:
                print(f"[Skip] Duplicate title: '{title}'")
                continue
            seen_titles.add(title)

            role = RoleTaxonomy(
                title=title,
                sector_id=it_sector.id,
                seniority=None,             # no seniority data in Excel
            )
            db.session.add(role)
            db.session.flush()
            roles_added += 1

            for skill_name in row['skills']:
                skill_id = skill_map.get(skill_name)
                if skill_id:
                    db.session.add(RoleSkill(role_id=role.id, skill_id=skill_id))
                    role_skills_added += 1

        db.session.commit()

        # ── 6. Summary ───────────────────────────────────────────────────
        print("\n=== Done! ===")
        print(f"  Sector   : 1  ({IT_SECTOR_NAME})")
        print(f"  Roles    : {roles_added}")
        print(f"  Skills   : {len(skill_map)}")
        print(f"  RoleSkill: {role_skills_added} links")


if __name__ == '__main__':
    seed()
