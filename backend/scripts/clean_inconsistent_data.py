import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.taxonomy import SectorTaxonomy, SectorAlias, RoleTaxonomy, SkillTaxonomy
from app.models.job import JobListing
from sqlalchemy import func

# Standard clean sectors we want to enforce
STANDARD_SECTORS = [
    "IT",
    "Data & AI",
    "Product Management",
    "Design",
    "Sales & Marketing",
    "Finance & Banking",
    "Human Resources",
    "Operations",
    "Legal",
    "Customer Success",
    "Other"
]

# Source sector name -> Target sector name mapping
MERGE_MAPPING = {
    "bt engineering services-779": "IT",
    "sw eng - infrastructure-672": "IT",
    "platforms engineering": "IT",
    "eng platforms": "IT",
    "sa": "IT",
    "field engineering": "IT",
    "ai research & engineering": "Data & AI",
    "data": "Data & AI",
    "web marketing-465": "Sales & Marketing",
    "sales": "Sales & Marketing",
    "marketing": "Sales & Marketing",
    "amer - commercial": "Sales & Marketing",
    "mid market": "Sales & Marketing"
}

def reset_sequences():
    print("Resetting database primary key sequences...")
    tables = [
        'sector_taxonomy',
        'role_taxonomy',
        'skill_taxonomy',
        'sector_alias',
        'role_alias',
        'skill_alias',
        'role_skill'
    ]
    for t in tables:
        try:
            # First check if the table exists by executing a quick query
            db.session.execute(db.text(f"SELECT 1 FROM {t} LIMIT 1;"))
            db.session.execute(db.text(
                f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(max(id), 1)) FROM {t};"
            ))
            print(f" -> Reset sequence for table '{t}'")
        except Exception as e:
            # Roll back block transaction error if any query failed
            db.session.rollback()
            print(f" -> Could not reset sequence for table '{t}' (might be normal if table doesn't have sequence or is empty): {e}")
    db.session.commit()

def run_migration():
    app = create_app()
    with app.app_context():
        # First reset sequences to avoid Postgres primary key constraints conflicts
        reset_sequences()
        
        print("\nStarting Sector Taxonomy Migration & Cleanup...")
        
        # 1. Ensure all standard sectors exist
        sector_objs = {}
        for name in STANDARD_SECTORS:
            sec = SectorTaxonomy.query.filter(func.lower(SectorTaxonomy.name) == name.lower()).first()
            if not sec:
                sec = SectorTaxonomy(name=name)
                db.session.add(sec)
                db.session.flush()
                print(f"Created standard sector: '{name}'")
            else:
                print(f"Standard sector exists: '{sec.name}'")
            sector_objs[name] = sec
            
        # Ensure 'Other' exists
        other_sector = sector_objs.get("Other")

        # 2. Perform merging of messy sectors
        all_db_sectors = SectorTaxonomy.query.all()
        for s in all_db_sectors:
            s_name_lower = s.name.lower().strip()
            if s.name in STANDARD_SECTORS:
                continue
                
            # Determine target sector
            target_name = MERGE_MAPPING.get(s_name_lower)
            if not target_name:
                # If not in explicit mapping, fallback to "Other"
                target_name = "Other"
                
            target_sec = sector_objs.get(target_name)
            if not target_sec:
                target_sec = other_sector
                
            print(f"\nMerging Sector '{s.name}' (ID={s.id}) into '{target_sec.name}' (ID={target_sec.id})...")
            
            # Update RoleTaxonomy references
            roles_updated = RoleTaxonomy.query.filter_by(sector_id=s.id).update({RoleTaxonomy.sector_id: target_sec.id})
            print(f" -> Updated {roles_updated} roles.")
            
            # Update SkillTaxonomy references
            skills_updated = SkillTaxonomy.query.filter_by(sector_id=s.id).update({SkillTaxonomy.sector_id: target_sec.id})
            print(f" -> Updated {skills_updated} skills.")
            
            # Update JobListing references
            jobs_updated = JobListing.query.filter_by(sector_id=s.id).update({JobListing.sector_id: target_sec.id})
            print(f" -> Updated {jobs_updated} jobs.")
            
            # Move SectorAliases
            target_aliases = {a.name.lower() for a in target_sec.aliases}
            
            # Add original sector name as alias of target sector so future imports map to target
            if s.name.lower() not in target_aliases:
                db.session.add(SectorAlias(name=s.name.lower(), sector_id=target_sec.id))
                target_aliases.add(s.name.lower())
                print(f" -> Added original sector name '{s.name.lower()}' as alias of '{target_sec.name}'")
                
            for alias in s.aliases:
                if alias.name.lower() not in target_aliases:
                    alias.sector_id = target_sec.id
                    print(f" -> Moved alias '{alias.name}' to '{target_sec.name}'")
                else:
                    db.session.delete(alias)
                    print(f" -> Deleted duplicate alias '{alias.name}'")
                    
            # Delete old sector
            db.session.delete(s)
            print(f" -> Deleted Sector '{s.name}'")
            db.session.flush()

        db.session.commit()
        
        # Invalidate data cache
        from app.services.data_normalizer import invalidate_cache
        invalidate_cache()
        print("\nSector Taxonomy Migration & Cleanup completed successfully!")

if __name__ == "__main__":
    run_migration()
