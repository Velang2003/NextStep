"""
Job aggregation pipeline:
- Calls all data sources: Greenhouse, Lever, Ashby + JobSpy (LinkedIn/Indeed)
- Three-level deduplication: (source, source_id) → title+company fingerprint → URL
- Persists unique raw payloads to job_raw staging table
- Recomputes SkillTrend, RoleTrend, and SectorTrend tables
"""

from datetime import datetime, timezone
from collections import Counter
from app import db
from app.models.job import JobListing, JobRaw, SkillTrend, RoleTrend, SectorTrend

from sqlalchemy import func, or_, text, tuple_
import threading
from app.services.cache_service import cached, cache_svc

# Global status for live admin tracking
pipeline_status = {
    'is_running': False,
    'step': 'Idle',
    'progress': 0,
    'total': 0,
    'logs': [],
    'results': None,
    'last_run': None
}
_status_lock = threading.Lock()

def _update_status(step=None, progress=None, total=None, log=None, logs=None, results=None, is_running=None):
    with _status_lock:
        if step is not None: pipeline_status['step'] = step
        if progress is not None: pipeline_status['progress'] = progress
        if total is not None: pipeline_status['total'] = total
        if is_running is not None: pipeline_status['is_running'] = is_running
        if results is not None: pipeline_status['results'] = results
        if logs is not None: pipeline_status['logs'] = logs
        if log:
            pipeline_status['logs'].append(f"[{datetime.now().strftime('%H:%M:%S')}] {log}")
            if len(pipeline_status['logs']) > 50:
                pipeline_status['logs'].pop(0)

def get_pipeline_status():
    with _status_lock:
        return pipeline_status.copy()


def run_pipeline() -> dict:
    """
    Unified Pipeline:
    1. Concurrent Fetch: Parallelize fetching from REST APIs and ATS boards.
    2. Batch Dedup: Remove cross-source duplicates in-memory.
    3. Staging: Save unique payloads to JobRaw.
    4. Processing: Trigger the integrated consumer to normalize listings and extract skills.
    """
    _update_status(is_running=True, step='Initializing', progress=0, total=0, logs=[], log="Starting unified pipeline run...")
    overall_start = datetime.now()
    
    results = {
        'fetched': 0, 'deduped': 0, 'inserted_raw': 0, 
        'processed': 0, 'new_listings': 0, 'errors': []
    }

    from app.services import (
        remotive_service, arbeitnow_service, themuse_service, jobicy_service,
        greenhouse_service, lever_service, ashby_service
    )
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from flask import current_app
    app = current_app._get_current_object()

    # Define all fetchers
    fetchers = [
        ('Remotive',  remotive_service.fetch_all),
        ('Arbeitnow', arbeitnow_service.fetch_all),
        ('The Muse',  themuse_service.fetch_all),
        ('Jobicy',    jobicy_service.fetch_all),
        ('Greenhouse', greenhouse_service.fetch_all),
        ('Lever',      lever_service.fetch_all),
        ('Ashby',      ashby_service.fetch_all),
    ]

    # Wrapper to push app context into each worker thread
    def _fetch_with_ctx(func):
        with app.app_context():
            return func()

    all_jobs: list[dict] = []
    
    # 1. Concurrent Fetch (60s timeout per source to prevent hangs)
    _update_status(step='Fetching Data', total=len(fetchers), log=f"Fetching from {len(fetchers)} sources...")
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(_fetch_with_ctx, func): name for name, func in fetchers}
        for i, fut in enumerate(as_completed(futures, timeout=300)):
            name = futures[fut]
            try:
                jobs = fut.result(timeout=300)
                all_jobs.extend(jobs)
                _update_status(progress=i+1, log=f"✓ {name}: {len(jobs)} jobs")
            except TimeoutError:
                msg = f"{name}: Timed out after 300s — skipped"
                results['errors'].append(msg)
                _update_status(progress=i+1, log=f"⏱ {msg}")
            except Exception as e:
                msg = f"{name} Fetch Error: {e}"
                results['errors'].append(msg)
                _update_status(progress=i+1, log=f"✗ {msg}")

    results['fetched'] = len(all_jobs)

    # 2. Batch Deduplication
    _update_status(step='Deduplicating', log=f"Running batch deduplication on {len(all_jobs)} jobs...")
    from app.services.deduplicator import deduplicate_batch
    unique_jobs, dedup_stats = deduplicate_batch(all_jobs)
    results['deduped'] = len(unique_jobs)

    # 3. Stage into JobRaw
    _update_status(step='Staging Raw Data', total=len(unique_jobs), log="Persisting unique jobs to JobRaw staging...")
    now = datetime.now(timezone.utc)
    raw_inserted = 0
    raw_refreshed = 0
    seen_keys = set()

    # Load existing raw jobs into a fast lookup map
    existing_raw_query = JobRaw.query.with_entities(
        JobRaw.source, JobRaw.source_id, JobRaw.raw_payload, JobRaw.is_processed
    ).all()
    existing_raw_map = {
        (r.source, r.source_id): (r.raw_payload, r.is_processed)
        for r in existing_raw_query
    }

    keys_to_update_fetched_at = []

    for j_idx, job in enumerate(unique_jobs):
        src, sid = job.get('source'), job.get('source_id')
        key = (src, sid)
        seen_keys.add(key)
        
        if key in existing_raw_map:
            old_payload, is_proc = existing_raw_map[key]
            
            # Detect payload changes to core fields to decide if we re-process
            payload_changed = False
            if isinstance(old_payload, dict):
                for f in ['title', 'description', 'company', 'location']:
                    if old_payload.get(f) != job.get(f):
                        payload_changed = True
                        break
            else:
                payload_changed = True
            
            if payload_changed:
                db.session.query(JobRaw).filter_by(source=src, source_id=sid).update(
                    {'raw_payload': job, 'fetched_at': now, 'is_processed': False},
                    synchronize_session=False
                )
                raw_refreshed += 1
            else:
                # If unmodified, only update the fetched_at timestamp
                keys_to_update_fetched_at.append(key)
        else:
            db.session.add(JobRaw(source=src, source_id=sid, raw_payload=job, fetched_at=now))
            raw_inserted += 1
        
        if (j_idx + 1) % 1000 == 0:
            _update_status(progress=j_idx+1)
            db.session.commit()

    db.session.commit()

    # Bulk update fetched_at timestamps for unmodified jobs in chunks to minimize network roundtrips
    if keys_to_update_fetched_at:
        chunk_size = 500
        for i in range(0, len(keys_to_update_fetched_at), chunk_size):
            chunk = keys_to_update_fetched_at[i:i+chunk_size]
            db.session.query(JobRaw).filter(
                tuple_(JobRaw.source, JobRaw.source_id).in_(chunk)
            ).update({'fetched_at': now}, synchronize_session=False)
            db.session.commit()

    results['inserted_raw'] = raw_inserted
    _update_status(log=f"Staging complete: {raw_inserted} new, {raw_refreshed} updated payloads.")

    # 4. Integrated Consumer Processing
    _update_status(step='Processing & Skill Extraction', log="Starting normalization and skill extraction...")
    consumer_stats = run_integrated_consumer()
    results.update(consumer_stats)

    # 5. Smart Cleanup
    _update_status(step='Cleaning Stale Data', log="Marking stale listings as expired...")
    if seen_keys:
        sources_in_run = {k[0] for k in seen_keys}
        total_expired = 0
        for src in sources_in_run:
            active_ids = {k[1] for k in seen_keys if k[0] == src}
            total_expired += db.session.query(JobListing).filter(
                JobListing.source == src,
                JobListing.status == 'active',
                ~JobListing.source_id.in_(active_ids)
            ).update({'status': 'expired'}, synchronize_session=False)
        
        db.session.commit()
        _update_status(log=f"Cleanup complete: {total_expired} expired.")

    # 6. Invalidate Trend & Job Cache
    _update_status(step='Finalizing', log="Invalidating stale caches...")
    cache_svc.clear_pattern("trends:*")
    cache_svc.clear_pattern("jobs:list:*")
    cache_svc.clear_pattern("user:*:recommended_roles")

    duration = (datetime.now() - overall_start).total_seconds()
    pipeline_status['last_run'] = datetime.now().isoformat()
    _update_status(is_running=False, step='Completed', results=results, log=f"Full run complete in {duration:.1f}s.")
    return results


def run_integrated_consumer() -> dict:
    """
    Normalized processing logic moved from scripts/process_raw_jobs.py to the core service.
    Processes all unprocessed JobRaw entries into JobListing.
    """
    from app.models.taxonomy import RoleSkill, SkillTaxonomy, SectorTaxonomy, RoleTaxonomy
    from app.services.data_normalizer import extract_skills, classify_department, normalize_role
    
    stats = {'processed': 0, 'new_listings': 0}
    discovery_count = 0
    
    # Pre-fetch taxonomy
    sectors_map = {s.name: s.id for s in SectorTaxonomy.query.all()}
    roles_map = {r.title: r.id for r in RoleTaxonomy.query.all()}
    skills_map = {s.canonical_name: s.id for s in SkillTaxonomy.query.all()}
    
    existing_listings = {
        (jl.source, jl.source_id): jl.id 
        for jl in JobListing.query.with_entities(JobListing.id, JobListing.source, JobListing.source_id).all()
    }

    role_skill_associations = {}
    for rs in RoleSkill.query.all():
        if rs.role_id not in role_skill_associations:
            role_skill_associations[rs.role_id] = set()
        role_skill_associations[rs.role_id].add(rs.skill_id)

    raw_jobs = JobRaw.query.filter_by(is_processed=False).all()
    if not raw_jobs:
        return stats

    for i, raw in enumerate(raw_jobs):
        if (i + 1) % 50 == 0:
            try:
                from app.services.pipeline import _update_status
                _update_status(progress=i+1, total=len(raw_jobs), log=f"Processing job {i+1}/{len(raw_jobs)}...")
            except ImportError:
                pass
                
        payload = raw.raw_payload
        title = payload.get('title', '')
        dept = payload.get('department', '')
        desc = payload.get('description', '') or ''
        
        sector_id = sectors_map.get(classify_department(title, dept))
        role_id = roles_map.get(normalize_role(title))
        listing_id = existing_listings.get((raw.source, raw.source_id))
        
        if listing_id:
            listing = db.session.get(JobListing, listing_id)
            if listing:
                listing.title = title
                listing.department = dept
                listing.sector_id = sector_id
                listing.role_id = role_id
                from app.models.job_skill import JobSkill
                JobSkill.query.filter_by(job_id=listing_id).delete()
        else:
            from app.models.job import JobListing as JL
            listing = JL(
                source=raw.source, source_id=raw.source_id,
                company=payload.get('company'), title=title,
                department=dept, location=payload.get('location'),
                country=payload.get('country'), remote=payload.get('remote', False),
                description=desc, url=payload.get('url'),
                sector_id=sector_id, role_id=role_id
            )
            db.session.add(listing)
            db.session.flush()
            listing_id = listing.id
            stats['new_listings'] += 1

        # Skill extraction
        from app.models.job_skill import JobSkill
        detected_skill_names = extract_skills(f"{title} {desc}")
        allowed_skill_ids = role_skill_associations.get(role_id, set()) if role_id else set()
        
        for skill_name in detected_skill_names:
            skill_id = skills_map.get(skill_name)
            if not skill_id: continue
            
            is_valid = False
            if skill_id in allowed_skill_ids: is_valid = True
            elif skill_name.lower() in title.lower(): is_valid = True
            elif desc.lower().count(skill_name.lower()) >= 1: is_valid = True
            elif not role_id: is_valid = True

            if is_valid:
                db.session.add(JobSkill(job_id=listing_id, skill_id=skill_id, proficiency_level='medium'))

        # Discovery Step: Identify potentially new skills/roles for Admin review
        # We only do this for jobs where normalization was weak to discover emerging trends
        # IMPORTANT: To prevent pipeline stalling during bulk sync, we limit this to a small subset
        # of jobs (max 15 per run) instead of disabling it completely when raw_jobs count is high.
        if (not role_id or len(detected_skill_names) < 3) and discovery_count < 100:
            try:
                discovery_count += 1
                from app.services.ai_service import ai_svc
                from app.models.taxonomy import PendingSkill, PendingRole, RoleTaxonomy, KeywordDiscovery
                discovery = ai_svc.discover_new_entities(f"{title} {desc}")
                
                # Discovery logic with Threshold (Frequency >= 5)
                # 1. New Role Candidate
                dr = discovery.get('role')
                if dr and len(dr) > 3:
                    if not RoleTaxonomy.query.filter(func.lower(RoleTaxonomy.title) == dr.lower()).first():
                        kd = KeywordDiscovery.query.filter_by(name=dr, type='role').first()
                        if kd:
                            kd.frequency += 1
                            if kd.frequency >= 2:
                                # Promote to Pending
                                if not PendingRole.query.filter_by(title=dr).first():
                                    db.session.add(PendingRole(
                                        title=dr,
                                        suggested_sector=dept or 'Other',
                                        source='pipeline',
                                        source_detail=f"Frequent Keyword (Seen 2+ times)"
                                    ))
                        else:
                            db.session.add(KeywordDiscovery(name=dr, type='role', suggested_sector=dept))
                
                # 2. New Skill Candidate
                for s in discovery.get('skills', []):
                    if len(s) > 2 and s.lower() not in [sk.lower() for sk in skills_map.keys()]:
                        kd = KeywordDiscovery.query.filter_by(name=s, type='skill').first()
                        if kd:
                            kd.frequency += 1
                            if kd.frequency >= 2:
                                # Promote to Pending
                                if not PendingSkill.query.filter_by(name=s).first():
                                    db.session.add(PendingSkill(
                                        name=s,
                                        suggested_category='Tool',
                                        source='pipeline',
                                        source_detail=f"Frequent Keyword (Seen 2+ times)"
                                    ))
                        else:
                            db.session.add(KeywordDiscovery(name=s, type='skill'))
    
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Discovery failed for job {title}: {e}")

        # MOVED OUTSIDE THE IF BLOCK: Mark as processed for EVERY job!
        raw.is_processed = True
        stats['processed'] += 1
        
        if (i + 1) % 100 == 0:
            db.session.commit()

    db.session.commit()
    
    # Recompute trends
    _recompute_skill_trends()
    _recompute_role_trends()
    _recompute_sector_trends()
    
    return stats



def _recompute_skill_trends():
    """Compute skill trends using sector-aware filtering (active jobs only).
    Only counts skills that belong to the same sector as the job, or cross-sector skills (sector_id IS NULL).
    """
    print("[Pipeline] Recomputing skill trends (sector-filtered, active jobs only)...")
    period = _current_period()
    SkillTrend.query.filter_by(period=period).delete()

    from app.models.job_skill import JobSkill
    from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy

    # Count skills per sector, only where the skill belongs to the same sector or is cross-sector
    rows = db.session.query(
        SectorTaxonomy.name,
        SkillTaxonomy.canonical_name,
        func.count(JobSkill.id).label('cnt')
    ).join(JobListing, JobSkill.job_id == JobListing.id)\
     .join(SectorTaxonomy, JobListing.sector_id == SectorTaxonomy.id)\
     .join(SkillTaxonomy, JobSkill.skill_id == SkillTaxonomy.id)\
     .filter(JobListing.status == 'active')\
     .filter(
         db.or_(
             SkillTaxonomy.sector_id == JobListing.sector_id,  # Same sector
             SkillTaxonomy.sector_id.is_(None)                 # Cross-sector skill
         )
     )\
     .group_by(SectorTaxonomy.name, SkillTaxonomy.canonical_name).all()

    for sector_name, skill_name, count in rows:
        if count > 0:
            db.session.add(SkillTrend(
                skill=skill_name, count=count, sector=sector_name, period=period
            ))

    db.session.commit()
    print(f"[Pipeline] Skill trends updated ({len(rows)} skill-sector pairs).")


def _recompute_role_trends():
    """Compute role frequency and TF-IDF demand from ACTIVE job titles."""
    _update_status(log="Recomputing role trends with TF-IDF weighting...")
    period = _current_period()
    RoleTrend.query.filter_by(period=period).delete()

    from app.models.taxonomy import RoleTaxonomy, SectorTaxonomy
    import math

    roles = RoleTaxonomy.query.all()
    total_sectors = SectorTaxonomy.query.count() or 1
    
    # 1. Frequency per Sector (relaxed filter: count role in ANY sector it appears)
    rows = db.session.query(
        SectorTaxonomy.name,
        RoleTaxonomy.title,
        func.count(JobListing.id).label('cnt')
    ).join(JobListing, JobListing.role_id == RoleTaxonomy.id)\
     .join(SectorTaxonomy, JobListing.sector_id == SectorTaxonomy.id)\
     .filter(JobListing.status == 'active')\
     .group_by(SectorTaxonomy.name, RoleTaxonomy.title).all()

    for sector_name, role_title, count in rows:
        if count > 0:
            db.session.add(RoleTrend(
                role_title=role_title,
                sector=sector_name,
                count=count,
                period=period,
            ))

    db.session.commit()
    _update_status(log=f"Role trends updated ({len(rows)} pairs).")


def _recompute_sector_trends():
    """Compute sector distribution with growth % vs previous period — ACTIVE jobs only."""
    print("[Pipeline] Recomputing sector trends (active jobs only)...")
    period = _current_period()
    prev_period = _previous_period()
    SectorTrend.query.filter_by(period=period).delete()

    # Current active sector counts (via sector_taxonomy FK)
    from app.models.taxonomy import SectorTaxonomy
    rows = db.session.query(
        SectorTaxonomy.name, func.count(JobListing.id).label('cnt')
    ).join(JobListing, JobListing.sector_id == SectorTaxonomy.id)\
     .filter(JobListing.status == 'active')\
     .group_by(SectorTaxonomy.name).all()

    # Previous period counts for growth calc (kept in sector_trends historical rows)
    prev_counts = {
        pr.sector: pr.total_jobs
        for pr in SectorTrend.query.filter_by(period=prev_period).all()
    }

    for sector_name, count in rows:
        prev  = prev_counts.get(sector_name, 0)
        growth = round(((count - prev) / prev * 100), 1) if prev > 0 else 0.0
        db.session.add(SectorTrend(
            sector=sector_name,
            total_jobs=count,
            growth_pct=growth,
            period=period,
        ))

    db.session.commit()
    print("[Pipeline] Sector trends updated.")

    db.session.commit()
    print("[Pipeline] Sector trends updated.")


def _current_period() -> str:
    now = datetime.now(timezone.utc)
    quarter = (now.month - 1) // 3 + 1
    return f"{now.year}-Q{quarter}"


def _previous_period() -> str:
    now = datetime.now(timezone.utc)
    quarter = (now.month - 1) // 3 + 1
    if quarter == 1:
        return f"{now.year - 1}-Q4"
    return f"{now.year}-Q{quarter - 1}"


@cached("trends:skills", timeout=86400) # 24h
def get_skill_trends(sector: str = None, limit: int = 20) -> list[dict]:
    """Return top skill trends, optionally filtered by sector."""
    if sector:
        trends = SkillTrend.query.filter_by(sector=sector).order_by(
            SkillTrend.count.desc()
        ).limit(limit).all()
        return [t.to_dict() for t in trends]
    else:
        rows = db.session.query(
            SkillTrend.skill, func.sum(SkillTrend.count).label('total_count')
        ).group_by(SkillTrend.skill).order_by(
            func.sum(SkillTrend.count).desc()
        ).limit(limit).all()
        return [{'skill': r[0], 'count': int(r[1]), 'sector': 'All Sectors'} for r in rows]


@cached("trends:roles", timeout=300) # 5 min cache for live consistency
def get_role_trends(sector: str = None, limit: int = 20) -> list[dict]:
    from app.models.job import JobListing
    from app.models.taxonomy import RoleTaxonomy, SectorTaxonomy
    period = _current_period()

    # Query live active jobs directly to ensure perfect consistency with Career Roadmap
    query = db.session.query(
        RoleTaxonomy.title,
        func.count(JobListing.id).label('total_count')
    ).join(JobListing, JobListing.role_id == RoleTaxonomy.id)\
     .filter(JobListing.status == 'active')

    if sector:
        # Filter by the Job's actual sector if requested
        query = query.join(SectorTaxonomy, JobListing.sector_id == SectorTaxonomy.id)\
                     .filter(SectorTaxonomy.name == sector)

    rows = query.group_by(RoleTaxonomy.title)\
                .order_by(func.count(JobListing.id).desc())\
                .limit(limit).all()

    return [
        {'role': r[0], 'count': int(r[1]), 'sector': sector or 'All Sectors', 'period': period}
        for r in rows
    ]


@cached("trends:sectors", timeout=86400)
def get_sector_trends() -> list[dict]:
    """Return sector breakdown with growth percentages."""
    period = _current_period()
    rows = SectorTrend.query.filter_by(period=period).order_by(
        SectorTrend.total_jobs.desc()
    ).all()
    if not rows:
        # Fallback: compute from job_listings directly
        from app.models.job import JobListing
        db_rows = db.session.query(
            JobListing.department, func.count(JobListing.id).label('count')
        ).filter(JobListing.status == 'active')\
         .group_by(JobListing.department).order_by(
            func.count(JobListing.id).desc()
        ).all()
        return [{'sector': r[0] or 'Other', 'total_jobs': r[1], 'growth_pct': 0, 'period': period} for r in db_rows]
    return [r.to_dict() for r in rows]


@cached("jobs:list", timeout=300) # 5 min cache for listings
def get_job_listings(filters: dict = None, page: int = 1, per_page: int = 20):
    """Paginated job listing query with optional filters. Defaults to active jobs."""
    query = JobListing.query.filter(JobListing.status == 'active')
    if filters:
        if filters.get('country'):
            query = query.filter(JobListing.country == filters['country'])
        if filters.get('remote') is not None:
            query = query.filter(JobListing.remote == filters['remote'])
        if filters.get('sector'):
            query = query.filter(JobListing.department.ilike(f"%{filters['sector']}%"))
        if filters.get('skill'):
            from app.models.job_skill import JobSkill
            from app.models.taxonomy import SkillTaxonomy
            query = query.join(JobSkill).join(SkillTaxonomy).filter(SkillTaxonomy.canonical_name.ilike(f"%{filters['skill']}%"))
        if filters.get('search'):
            q = filters['search']
            # MySQL Full-Text Search (Fallback to LIKE for other DBs)
            if db.engine.name == 'mysql':
                query = query.filter(
                    text("MATCH(title, company, location, description) AGAINST(:search IN BOOLEAN MODE)")
                ).params(search=f"{q}*")
            else:
                q_like = f"%{q}%"
                query = query.filter(
                    or_(
                        JobListing.title.ilike(q_like),
                        JobListing.company.ilike(q_like),
                        JobListing.location.ilike(q_like),
                        JobListing.description.ilike(q_like),
                    )
                )
    paginated = query.order_by(JobListing.fetched_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return {
        'jobs':     [j.to_dict() for j in paginated.items],
        'total':    paginated.total,
        'page':     page,
        'per_page': per_page,
        'pages':    paginated.pages,
    }
