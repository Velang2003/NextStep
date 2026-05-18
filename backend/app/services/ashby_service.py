"""
Ashby Public Job Listing API Service
Endpoint: https://api.ashbyhq.com/posting-api/job-board/
"""

import requests
from datetime import datetime, timezone
from .data_normalizer import extract_skills, normalize_location, classify_department

ASHBY_REST_URL = "https://api.ashbyhq.com/posting-api/job-board/"

# Verified-live Ashby public job boards (32 companies)
COMPANIES = [
    # Core
    'ycombinator', 'vanta', 'replit', 'supabase', 'render', 'linear',
    'quora', 'cohere', 'notion', 'pinecone',

    # AI / LLM
    'mistral', 'perplexity', 'anyscale', 'modal', 'baseten', 'elevenlabs',

    # Developer Tools / Infra
    'neon', 'inngest', 'resend', 'plain', 'paragon', 'graphite',

    # Data & Analytics
    'materialize', 'cube', 'lightdash',

    # Security & Compliance
    'drata', 'oneleet',

    # HR Tech
    'leapsome', 'humaans', 'oyster',

    # Product & Growth
    'posthog',

    # Climate
    'watershed',
]



def _strip_html(html: str) -> str:
    import re
    return re.sub(r'<[^>]+>', ' ', html or '')


def fetch_company_jobs(company_name: str) -> list[dict]:
    """Fetch and normalize all jobs from a single Ashby board."""
    slug = company_name.lower().replace(' ', '-').replace('.', '')
    try:
        resp = requests.get(f"{ASHBY_REST_URL}{slug}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code != 200:
            print(f"  [Ashby] {company_name}: HTTP {resp.status_code}")
            return []
        
        data = resp.json()
        jobs_raw = data.get('jobs', [])
        normalized = []
        
        for job in jobs_raw:
            plain_text = job.get('descriptionPlain', '') or _strip_html(job.get('descriptionHtml', ''))
            location_raw = job.get('location', '')
            loc = normalize_location(location_raw)
            dept = job.get('department', '')

            posted_at = None
            pub = job.get('publishedAt')
            if pub:
                try:
                    posted_at = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                except Exception:
                    pass

            normalized.append({
                'source':          'ashby',
                'source_id':       job.get('id', ''),
                'company':         company_name,
                'title':           job.get('title', ''),
                'department':      dept,
                'sector':          classify_department(job.get('title', ''), dept),
                'location':        loc['location'],
                'country':         loc['country'],
                'remote':          loc['remote'],
                'employment_type': job.get('employmentType', 'Full-time'),
                'skills_required': extract_skills(plain_text),
                'url':             job.get('jobUrl') or job.get('applyUrl') or f"https://jobs.ashbyhq.com/{slug}/{job.get('id', '')}",
                'posted_at':       posted_at.isoformat() if posted_at else None,
            })
        return normalized
    except requests.RequestException as e:
        print(f"  [Ashby] {company_name} request error: {e}")
        return []


def fetch_all() -> list[dict]:
    """Fetch jobs from all configured Ashby company boards (parallel)."""
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
    print(f"  [Ashby] Total: {len(all_jobs)} jobs from {len(COMPANIES)} boards")
    return all_jobs
