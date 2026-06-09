"""
Greenhouse Public Board API Service
Endpoint: https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true
No API key required for public job boards.
"""

import requests
from datetime import datetime, timezone
from .data_normalizer import extract_skills, normalize_location, classify_department

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"

# Tech companies with verified-live public Greenhouse boards (55 companies)
COMPANIES = [
    # Top-tier tech
    'airbnb', 'stripe', 'figma', 'gitlab', 'cloudflare', 'vercel',
    'pinterest', 'discord', 'datadog', 'lyft', 'monzo', 'asana',
    'duolingo', 'robinhood', 'dropbox', 'twilio', 'intercom', 'okta',
    'elastic', 'mongodb', 'samsara', 'brex', 'gusto', 'carta',
    'chime', 'blend',

    # AI / ML
    'anthropic',

    # Cloud & DevOps
    'fastly', 'netlify', 'planetscale',

    # SaaS / Productivity
    'airtable', 'webflow',

    # Fintech / Payments
    'adyen', 'mercury', 'remote',

    # E-commerce
    'klaviyo', 'yotpo', 'postscript',

    # Data & Analytics
    'amplitude', 'mixpanel', 'hightouch', 'fivetran', 'starburst', 'dremio',

    # Healthcare
    'cerebral', 'transcarent',

    # EdTech
    'coursera', 'masterclass', 'outschool',

    # Indian tech
    'groww',

    # Gaming
    'roblox', 'unity3d', 'scopely',

    # Infrastructure
    'tailscale',
]



def fetch_company_jobs(company_slug: str) -> list[dict]:
    """Fetch and normalize all jobs from a single Greenhouse board."""
    url = GREENHOUSE_API.format(company=company_slug)
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            print(f"  [Greenhouse] {company_slug}: HTTP {resp.status_code}")
            return []
        data = resp.json()
        jobs_raw = data.get('jobs', [])
        normalized = []
        for job in jobs_raw:
            content = job.get('content', '') or ''
            location_raw = ', '.join(
                [loc.get('name', '') for loc in job.get('offices', [])]
            ) or job.get('location', {}).get('name', '')
            loc = normalize_location(location_raw)
            dept = (job.get('departments') or [{}])[0].get('name', '')

            posted_at = None
            if job.get('updated_at'):
                try:
                    posted_at = datetime.fromisoformat(
                        job['updated_at'].replace('Z', '+00:00')
                    )
                except Exception:
                    pass

            normalized.append({
                'source':          'greenhouse',
                'source_id':       str(job.get('id', '')),
                'company':         company_slug.title(),
                'title':           job.get('title', ''),
                'department':      dept,
                'sector':          classify_department(job.get('title', ''), dept),
                'location':        loc['location'],
                'country':         loc['country'],
                'remote':          loc['remote'],
                'employment_type': 'Full-time',
                'skills_required': extract_skills(content),
                'url':             job.get('absolute_url', ''),
                'posted_at':       posted_at.isoformat() if posted_at else None,
            })
        return normalized
    except requests.RequestException as e:
        print(f"  [Greenhouse] {company_slug} request error: {e}")
        return []


def fetch_all() -> list[dict]:
    """Fetch jobs from all configured Greenhouse company boards (parallel)."""
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
        for fut in as_completed(futures, timeout=300):
            try:
                jobs = fut.result(timeout=15)
                all_jobs.extend(jobs)
            except Exception:
                pass
    print(f"  [Greenhouse] Total: {len(all_jobs)} jobs from {len(COMPANIES)} boards")
    return all_jobs
