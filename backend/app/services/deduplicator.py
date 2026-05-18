"""
deduplicator.py
===============
Cross-source deduplication utility for the NextStep job pipeline.

Problem:
  The same job posting often appears across multiple sources:
    - A company posts on LinkedIn AND Indeed → JobSpy picks it up twice
    - A company uses Greenhouse AND posts the same role on LinkedIn
    - The pipeline runs again next week → same jobs re-inserted

Existing guard (Level 1):
  pipeline.py already deduplicates by (source, source_id) — catches exact
  matches within the same source.

New guards (Levels 2 & 3):
  Level 2 — Title + Company fingerprint:
    Normalizes title + company → MD5 fingerprint.
    Two jobs with the same role at the same company (from different sources)
    are treated as duplicates. The FIRST inserted wins.

  Level 3 — URL domain deduplication:
    If two jobs share the exact apply URL, they are the same posting.

Usage in pipeline:
    from app.services.deduplicator import deduplicate_batch, cross_source_deduplicate_db

    # Before inserting into job_raw:
    clean_jobs = deduplicate_batch(all_jobs)

    # Optionally call after processing to clean up job_raw table:
    cross_source_deduplicate_db()
"""

import re
import hashlib
from app import db
from app.models.job import JobRaw


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalise_text(text: str) -> str:
    """
    Lowercase, remove punctuation, collapse whitespace.
    'Sr. Software Engineer - Backend (Python)' → 'sr software engineer backend python'
    """
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


_TITLE_NOISE = re.compile(
    r'\b(senior|sr|junior|jr|lead|principal|staff|associate|mid|entry|level|'
    r'i|ii|iii|iv|remote|hybrid|contract|temp|part.time|full.time)\b'
)

def _normalise_title(title: str) -> str:
    """
    Normalise a job title for deduplication — remove only true noise words
    (location hints, work-type labels) but KEEP seniority levels.
    
    'Senior Software Engineer - Backend (Remote)' → 'senior software engineer backend'
    'Junior Software Engineer - Backend'          → 'junior software engineer backend'
    These are DIFFERENT jobs and must NOT be deduplicated together.
    """
    t = _normalise_text(title)
    # Only strip location / work-type noise, not seniority
    t = re.sub(r'\b(remote|hybrid|contract|temp|part.time|full.time|onsite|on.site)\b', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def _normalise_company(company: str) -> str:
    """
    Normalise company name: strip 'Inc', 'Ltd', 'LLC', whitespace etc.
    'Stripe, Inc.' → 'stripe'
    """
    c = _normalise_text(company)
    c = re.sub(r'\b(inc|ltd|llc|corp|co|pvt|private|limited|group|holdings)\b', '', c)
    return re.sub(r'\s+', ' ', c).strip()


# ---------------------------------------------------------------------------
# Fingerprint generation
# ---------------------------------------------------------------------------

def generate_fingerprint(job: dict) -> str:
    """
    Generate an MD5 fingerprint for a job dict based on normalised
    title + company. Used for Level-2 cross-source deduplication.
    """
    title   = _normalise_title(job.get('title', ''))
    company = _normalise_company(job.get('company', ''))
    raw     = f"{title}||{company}"
    return hashlib.md5(raw.encode()).hexdigest()


def generate_url_fingerprint(job: dict) -> str | None:
    """
    Generate a fingerprint from the job URL (Level 3).
    Returns None if URL is absent or generic.
    """
    url = (job.get('url') or '').strip()
    if not url or len(url) < 10:
        return None
    # Normalise: strip query params that vary by referral source
    url_clean = re.sub(r'[?#].*$', '', url).rstrip('/')
    return hashlib.md5(url_clean.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Batch deduplication (runs BEFORE inserting into job_raw)
# ---------------------------------------------------------------------------

def deduplicate_batch(jobs: list[dict]) -> tuple[list[dict], dict]:
    """
    Deduplicate a list of job dicts fetched in the current pipeline run.

    Deduplication order:
      1. (source, source_id) exact match — cheapest check
      2. Title + company fingerprint — catches cross-source same job
      3. URL fingerprint — catches same posting, different referrer URL

    Returns:
      (unique_jobs, stats)
        unique_jobs — deduplicated list
        stats       — {'total': N, 'kept': K, 'removed': R, 'by_source_id': X,
                        'by_fingerprint': Y, 'by_url': Z}
    """
    seen_source_ids   : set[str] = set()
    seen_fingerprints : set[str] = set()
    seen_url_fps      : set[str] = set()

    unique: list[dict] = []
    stats = {'total': len(jobs), 'kept': 0, 'removed': 0,
             'by_source_id': 0, 'by_fingerprint': 0, 'by_url': 0}

    for job in jobs:
        # Level 1: exact (source, source_id)
        sid_key = f"{job.get('source')}|{job.get('source_id')}"
        if sid_key in seen_source_ids:
            stats['by_source_id'] += 1
            stats['removed'] += 1
            continue
        seen_source_ids.add(sid_key)

        # Level 2: title+company fingerprint
        fp = generate_fingerprint(job)
        if fp in seen_fingerprints:
            stats['by_fingerprint'] += 1
            stats['removed'] += 1
            continue
        seen_fingerprints.add(fp)

        # Level 3: URL fingerprint
        url_fp = generate_url_fingerprint(job)
        if url_fp and url_fp in seen_url_fps:
            stats['by_url'] += 1
            stats['removed'] += 1
            continue
        if url_fp:
            seen_url_fps.add(url_fp)

        unique.append(job)
        stats['kept'] += 1

    return unique, stats


# ---------------------------------------------------------------------------
# DB-level deduplication (runs against the job_raw staging table)
# ---------------------------------------------------------------------------

def cross_source_deduplicate_db() -> dict:
    """
    Scan the job_raw table and remove duplicate raw rows that survived
    previous pipeline runs.

    Strategy:
      - Build fingerprint for every row in job_raw
      - For each fingerprint seen more than once, keep the EARLIEST row
        (smallest id) and delete the rest
      - This is safe to call multiple times (idempotent)

    Returns stats dict.
    """
    print("[Deduplicator] Starting DB-level cross-source deduplication...")

    raw_jobs = JobRaw.query.order_by(JobRaw.id.asc()).all()
    fp_to_id: dict[str, int] = {}     # fingerprint → first job_raw.id
    to_delete: list[int] = []

    for raw in raw_jobs:
        payload = raw.raw_payload or {}
        fp = generate_fingerprint(payload)
        url_fp = generate_url_fingerprint(payload)

        is_dup = False

        if fp in fp_to_id:
            is_dup = True
        elif url_fp and url_fp in fp_to_id.values():
            is_dup = True

        if is_dup:
            to_delete.append(raw.id)
        else:
            fp_to_id[fp] = raw.id
            if url_fp:
                fp_to_id[url_fp] = raw.id  # reuse same dict for URL fps

    if to_delete:
        JobRaw.query.filter(JobRaw.id.in_(to_delete)).delete(synchronize_session=False)
        db.session.commit()
        print(f"[Deduplicator] Removed {len(to_delete)} duplicate raw rows from DB.")
    else:
        print("[Deduplicator] No duplicates found in DB.")

    stats = {
        'scanned': len(raw_jobs),
        'duplicates_removed': len(to_delete),
        'unique_remaining': len(raw_jobs) - len(to_delete),
    }
    return stats
