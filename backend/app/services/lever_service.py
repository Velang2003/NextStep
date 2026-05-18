"""
Lever Public Postings API Service
Endpoint: https://api.lever.co/v0/postings/{company}?mode=json
No API key required for public postings.
"""

import requests
from datetime import datetime, timezone
from .data_normalizer import extract_skills, normalize_location, classify_department

LEVER_API = "https://api.lever.co/v0/postings/{company}?mode=json"

# Verified-live Lever public job boards (3 companies)
COMPANIES = [
    'spotify', 'iterative', 'ro',
]



def fetch_company_jobs(company_slug: str) -> list[dict]:
    """Fetch and normalize all jobs from a single Lever board."""
    url = LEVER_API.format(company=company_slug)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"  [Lever] {company_slug}: HTTP {resp.status_code}")
            return []
        jobs_raw = resp.json()
        if not isinstance(jobs_raw, list):
            return []
        normalized = []
        for job in jobs_raw:
            content_blocks = job.get('descriptionBody', '') or ''
            lists_text = ' '.join(
                item for block in job.get('lists', [])
                for item in ([block.get('content', '')] if isinstance(block, dict) else [])
            )
            full_text = f"{content_blocks} {lists_text}"
            dept = job.get('categories', {}).get('department', '')
            location_raw = job.get('categories', {}).get('location', '')
            loc = normalize_location(location_raw)

            posted_at = None
            ts = job.get('createdAt')
            if ts:
                try:
                    posted_at = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                except Exception:
                    pass

            normalized.append({
                'source':          'lever',
                'source_id':       job.get('id', ''),
                'company':         company_slug.replace('-', ' ').title(),
                'title':           job.get('text', ''),
                'department':      dept,
                'sector':          classify_department(job.get('text', ''), dept),
                'location':        loc['location'],
                'country':         loc['country'],
                'remote':          loc['remote'],
                'employment_type': job.get('categories', {}).get('commitment', 'Full-time'),
                'skills_required': extract_skills(full_text),
                'url':             job.get('hostedUrl', ''),
                'posted_at':       posted_at.isoformat() if posted_at else None,
            })
        return normalized
    except requests.RequestException as e:
        print(f"  [Lever] {company_slug} request error: {e}")
        return []


def fetch_all() -> list[dict]:
    """Fetch jobs from all configured Lever company boards (parallel)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    try:
        from flask import current_app
        app = current_app._get_current_object()
    except RuntimeError:
        app = None

    def _fetch_with_ctx(company):
        if app:
            with app.app_context():
                return fetch_company_jobs(company)
        return fetch_company_jobs(company)

    all_jobs = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_with_ctx, c): c for c in COMPANIES}
        for fut in as_completed(futures, timeout=120):
            try:
                jobs = fut.result(timeout=15)
                all_jobs.extend(jobs)
            except Exception:
                pass
    print(f"  [Lever] Total: {len(all_jobs)} jobs from {len(COMPANIES)} boards")
    return all_jobs
