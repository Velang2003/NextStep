"""
Adzuna India API Service — https://api.adzuna.com/v1/api/jobs/in/search/
Free tier: 2,500 calls/month.
Strategy: Focused keyword queries, strict timeouts, non-blocking on rate limits.
"""
import requests
import os
import time
import logging
from .data_normalizer import classify_department, normalize_location

logger = logging.getLogger(__name__)

APP_ID  = os.environ.get('ADZUNA_APP_ID', '')
APP_KEY = os.environ.get('ADZUNA_APP_KEY', '')
BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search"

# Reduced query list — stays well within 2500 calls/month
# 8 keywords × 2 pages = 16 calls per run → ~156 runs/month budget
SEARCH_QUERIES = [
    "software engineer",
    "data scientist",
    "machine learning",
    "devops engineer",
    "full stack developer",
    "product manager",
    "data analyst",
    "cloud architect",
]

RESULTS_PER_PAGE = 50
MAX_PAGES = 2       # Reduced from 3 → faster, lower quota usage
REQUEST_TIMEOUT = 15  # Hard timeout per HTTP request
DELAY_SECS = 0.5    # Reduced from 1.0s


def _fetch_query(what: str = "", where: str = "India") -> list[dict]:
    """Fetch paginated results for a single keyword. Hard timeout on each HTTP call."""
    if not APP_ID or not APP_KEY:
        return []
    out = []
    try:
        for page in range(1, MAX_PAGES + 1):
            params = {
                'app_id':           APP_ID,
                'app_key':          APP_KEY,
                'results_per_page': RESULTS_PER_PAGE,
                'content-type':     'application/json',
                'sort_by':          'date',
            }
            if what:
                params['what'] = what
            if where:
                params['where'] = where

            url = f"{BASE_URL}/{page}"
            try:
                resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            except requests.exceptions.Timeout:
                logger.warning(f"[Adzuna] Timeout on '{what}' page {page} — skipping rest")
                break
            except requests.exceptions.RequestException as req_err:
                logger.warning(f"[Adzuna] Request error on '{what}': {req_err} — skipping")
                break

            if resp.status_code == 429:
                # Do NOT sleep 60s — just stop this keyword and move on
                logger.warning("[Adzuna] Rate limit hit — stopping this keyword")
                break
            if resp.status_code != 200:
                logger.warning(f"[Adzuna] HTTP {resp.status_code} for '{what}' — stopping pagination")
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
                    'description':     j.get('description', '')[:4000],  # Trimmed for speed
                    'url':             j.get('redirect_url', ''),
                    'posted_at':       j.get('created', None),
                    'salary_min':      j.get('salary_min'),
                    'salary_max':      j.get('salary_max'),
                })
            time.sleep(DELAY_SECS)

    except Exception as e:
        logger.error(f"[Adzuna] Error ('{what}'): {e}")
    return out


def fetch_all() -> list[dict]:
    """
    Fetch jobs from Adzuna India.
    Runs keyword-specific queries. Deduplicates by source_id.
    Designed to complete within ~90 seconds total.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    if not APP_ID or not APP_KEY:
        logger.info("[Adzuna] No API credentials configured — skipping.")
        return []

    all_jobs: list[dict] = []
    seen_ids: set = set()

    # Keyword-specific queries in parallel
    logger.info("[Adzuna] Starting parallel keyword sweep...")
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_fetch_query, kw, "India"): kw for kw in SEARCH_QUERIES}
        for fut in as_completed(futures, timeout=120):
            kw = futures[fut]
            try:
                batch = fut.result()
                added = 0
                for job in batch:
                    sid = job['source_id']
                    if sid and sid not in seen_ids:
                        seen_ids.add(sid)
                        all_jobs.append(job)
                        added += 1
                logger.info(f"[Adzuna] '{kw}': +{added} new jobs (total {len(all_jobs)})")
            except Exception as e:
                logger.error(f"[Adzuna] Error fetching keyword '{kw}': {e}")

    logger.info(f"[Adzuna] Total: {len(all_jobs)} unique Indian jobs fetched")
    return all_jobs
