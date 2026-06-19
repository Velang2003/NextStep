"""
Adzuna India API Service — https://api.adzuna.com/v1/api/jobs/in/search/
Free tier: 2,500 calls/month. Country code = 'in' for India.
Strategy: Paginate top-level India search + keyword-specific queries for max coverage
within the monthly quota. Conservatively uses ~60 calls per run (fits 40+ runs/month).
"""
import requests
import os
import time
from .data_normalizer import classify_department, normalize_location

APP_ID  = os.environ.get('ADZUNA_APP_ID', '')
APP_KEY = os.environ.get('ADZUNA_APP_KEY', '')
BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search"

# We use broad keyword groups to stay within the free quota
# Each group = ~3 pages × 50 results = 150 jobs per keyword
SEARCH_QUERIES = [
    # Tech engineering
    "software engineer",
    "data scientist",
    "machine learning",
    "devops engineer",
    "cloud architect",
    "full stack developer",
    # Business & product
    "product manager",
    "business analyst",
    "data analyst",
    # Design & management
    "ui ux designer",
    "project manager",
    "technical lead",
]

RESULTS_PER_PAGE = 50
MAX_PAGES = 3       # 3 pages × 50 = 150 per keyword — stays within free quota
DELAY_SECS = 1.0    # Adzuna recommends polite delays


def _fetch_query(what: str = "", where: str = "") -> list[dict]:
    """Fetch paginated results for a single keyword + optional city filter."""
    if not APP_ID or not APP_KEY:
        return []
    out = []
    try:
        for page in range(1, MAX_PAGES + 1):
            params = {
                'app_id':          APP_ID,
                'app_key':         APP_KEY,
                'results_per_page': RESULTS_PER_PAGE,
                'content-type':    'application/json',
                'sort_by':         'date',
            }
            if what:
                params['what'] = what
            if where:
                params['where'] = where

            url = f"{BASE_URL}/{page}"
            resp = requests.get(url, params=params, timeout=20)

            if resp.status_code == 429:
                print(f"  [Adzuna] Rate limit hit — pausing 60s")
                time.sleep(60)
                continue
            if resp.status_code != 200:
                print(f"  [Adzuna] HTTP {resp.status_code} for '{what}' — stopping pagination")
                break

            data = resp.json()
            jobs = data.get('results', [])
            if not jobs:
                break

            for j in jobs:
                loc_str  = j.get('location', {}).get('display_name', 'India')
                loc      = normalize_location(loc_str)
                title    = j.get('title', '')
                category = j.get('category', {}).get('label', '')
                contract = j.get('contract_time', 'full_time').replace('_', ' ').title()

                out.append({
                    'source':          'adzuna',
                    'source_id':       str(j.get('id', '')),
                    'company':         j.get('company', {}).get('display_name', ''),
                    'title':           title,
                    'department':      category,
                    'sector':          classify_department(title, category),
                    'location':        loc_str,
                    'country':         loc.get('country') or 'India',
                    'remote':          False,
                    'employment_type': contract,
                    'description':     j.get('description', '')[:8000],
                    'url':             j.get('redirect_url', ''),
                    'posted_at':       j.get('created', None),
                    'salary_min':      j.get('salary_min'),
                    'salary_max':      j.get('salary_max'),
                })
            time.sleep(DELAY_SECS)
    except Exception as e:
        print(f"  [Adzuna] Error ('{what}'): {e}")
    return out


def fetch_all() -> list[dict]:
    """
    Fetch jobs from Adzuna India.
    Runs broad sweep + keyword-specific queries. Deduplicates by source_id.
    """
    if not APP_ID or not APP_KEY:
        print("  [Adzuna] No API credentials configured — skipping.")
        return []

    all_jobs: list[dict] = []
    seen_ids: set = set()

    def _add_batch(batch):
        added = 0
        for job in batch:
            sid = job['source_id']
            if sid and sid not in seen_ids:
                seen_ids.add(sid)
                all_jobs.append(job)
                added += 1
        return added

    # 1. Broad India sweep (no keyword filter)
    print("  [Adzuna] Running broad India sweep...")
    broad = _fetch_query(what="", where="India")
    _add_batch(broad)
    print(f"  [Adzuna] Broad sweep: {len(all_jobs)} jobs")

    # 2. Keyword-specific queries
    for i, keyword in enumerate(SEARCH_QUERIES):
        batch = _fetch_query(what=keyword, where="India")
        added = _add_batch(batch)
        print(f"  [Adzuna] '{keyword}': +{added} new jobs (total {len(all_jobs)})")

    print(f"  [Adzuna] Total: {len(all_jobs)} unique Indian jobs fetched")
    return all_jobs
