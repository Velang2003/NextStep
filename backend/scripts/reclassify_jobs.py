"""
Reclassify Jobs Script
======================
Re-runs sector classification on all jobs currently tagged as "Other"
using the enriched sector aliases from the taxonomy database.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.taxonomy import SectorTaxonomy
from app.models.job import JobListing
from app.services.data_normalizer import classify_department, invalidate_cache

app = create_app()

def run():
    with app.app_context():
        # Force reload of taxonomy cache to pick up new Finance aliases
        invalidate_cache()

        other = SectorTaxonomy.query.filter_by(name='Other').first()
        if not other:
            print("No 'Other' sector found.")
            return

        # Build sector name → id lookup
        sectors = {s.name: s.id for s in SectorTaxonomy.query.all()}
        print(f"Sectors available: {list(sectors.keys())}")

        jobs = JobListing.query.filter_by(sector_id=other.id).all()
        print(f"\nReclassifying {len(jobs)} 'Other' jobs...")

        reclassified = {}
        for job in jobs:
            dept = job.department or ''
            title = job.title or ''
            desc_snippet = (job.description or '')[:300]

            # Use title + department + first 300 chars of description for better matching
            new_sector_name = classify_department(title, f"{dept} {desc_snippet}")

            if new_sector_name != 'Other' and new_sector_name in sectors:
                job.sector_id = sectors[new_sector_name]
                reclassified[new_sector_name] = reclassified.get(new_sector_name, 0) + 1

        db.session.commit()

        print(f"\nReclassification Results:")
        total = 0
        for name, count in sorted(reclassified.items(), key=lambda x: -x[1]):
            print(f"  {name}: {count} jobs moved")
            total += count
        print(f"\nTotal reclassified: {total}")
        print(f"Remaining in 'Other': {len(jobs) - total}")


if __name__ == '__main__':
    run()
