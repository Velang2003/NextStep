"""
Jooble API Service — https://jooble.org/api/about
Free API. Aggregates 50+ Indian job boards (Naukri, Shine, TimesJobs, Indeed India, LinkedIn India, etc.)
Strategy: Query with a matrix of top roles × Indian cities to maximize unique job coverage.
"""
import requests
import os
import time
import hashlib
from .data_normalizer import classify_department, normalize_location

API_KEY = os.environ.get('JOOBLE_API_KEY', '')
API_URL = f"https://jooble.org/api/{API_KEY}"

# Top tech roles relevant to the Indian market
KEYWORDS = [
    "Software Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "Data Analyst",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Product Manager",
    "Business Analyst",
    "Python Developer",
    "Java Developer",
    "React Developer",
    "Mobile App Developer",
    "UI UX Designer",
    "Cybersecurity Analyst",
    "QA Engineer",
    "Systems Architect",
    "Technical Lead",
]

# Major Indian tech hubs
LOCATIONS = [
    "Bangalore",
    "Hyderabad",
    "Mumbai",
    "Delhi",
    "Pune",
    "Chennai",
]

MAX_PAGES = 2        # 2 pages × 20 results = 40 jobs per query
DELAY_SECS = 0.5    # Polite delay between requests


def _make_source_id(job: dict) -> str:
    """Create a stable unique ID from job data since Jooble lacks a consistent ID field."""
    raw = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('link', '')}"
    return "jooble_" + hashlib.md5(raw.encode()).hexdigest()[:16]


def _fetch_batch(keyword: str, location: str) -> list[dict]:
    """Fetch one page batch for a keyword + location pair."""
    if not API_KEY:
        return []
    out = []
    try:
        for page in range(1, MAX_PAGES + 1):
            payload = {
                "keywords": keyword,
                "location": location,
                "page": page,
                "resultonpage": 20,
            }
            resp = requests.post(API_URL, json=payload, timeout=15)
            if resp.status_code != 200:
                break
            data = resp.json()
            jobs = data.get('jobs', [])
            if not jobs:
                break
            for j in jobs:
                loc_str = j.get('location', location)
                loc = normalize_location(loc_str)
                title = j.get('title', '')
                dept = ''
                out.append({
                    'source':          'jooble',
                    'source_id':       _make_source_id(j),
                    'company':         j.get('company', ''),
                    'title':           title,
                    'department':      dept,
                    'sector':          classify_department(title, dept),
                    'location':        loc_str,
                    'country':         loc.get('country') or 'India',
                    'remote':          False,
                    'employment_type': j.get('type', 'Full-time'),
                    'description':     j.get('snippet', '')[:8000],
                    'url':             j.get('link', ''),
                    'posted_at':       j.get('updated', None),
                    'salary_min':      None,
                    'salary_max':      None,
                })
            time.sleep(DELAY_SECS)
    except Exception as e:
        print(f"  [Jooble] Error ({keyword}/{location}): {e}")
    return out


def fetch_all() -> list[dict]:
    """
    Fetch jobs from Jooble across a matrix of keywords × Indian cities.
    Deduplicates by source_id before returning.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    if not API_KEY:
        print("  [Jooble] No API key configured — skipping.")
        return []

    all_jobs: list[dict] = []
    seen_ids: set = set()

    # Broad India sweep first (catches jobs from smaller cities too)
    print(f"  [Jooble] Starting broad India sweep...")
    broad = _fetch_batch("", "India")
    for job in broad:
        if job['source_id'] not in seen_ids:
            seen_ids.add(job['source_id'])
            all_jobs.append(job)

    # Keyword-specific sweep (India wide) in parallel
    print(f"  [Jooble] Starting parallel keyword sweep...")
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(_fetch_batch, kw, "India"): kw for kw in KEYWORDS}
        for fut in as_completed(futures, timeout=120):
            kw = futures[fut]
            try:
                batch = fut.result()
                for job in batch:
                    if job['source_id'] not in seen_ids:
                        seen_ids.add(job['source_id'])
                        all_jobs.append(job)
            except Exception as e:
                print(f"  [Jooble] Error fetching keyword {kw}: {e}")

    print(f"  [Jooble] Total: {len(all_jobs)} unique Indian jobs fetched")
    return all_jobs
