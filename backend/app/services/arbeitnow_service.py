"""
Arbeitnow API Service — https://arbeitnow.com/api/job-board-api
Free, no API key. Returns EU/global jobs with skill tags. Paginates up to 10 pages.
"""
import requests
from .data_normalizer import classify_department, normalize_location

API_URL = "https://arbeitnow.com/api/job-board-api"
MAX_PAGES = 10

def fetch_all() -> list[dict]:
    out = []
    try:
        for page in range(1, MAX_PAGES + 1):
            resp = requests.get(API_URL, params={'page': page}, timeout=15)
            if resp.status_code != 200:
                break
            data = resp.json()
            jobs = data.get('data', [])
            if not jobs:
                break
            for j in jobs:
                tags = j.get('tags', [])
                dept = tags[0] if tags else ''
                loc  = normalize_location(j.get('location', ''))
                out.append({
                    'source':          'arbeitnow',
                    'source_id':       j.get('slug', '') or str(hash(j.get('url', ''))),
                    'company':         j.get('company_name', ''),
                    'title':           j.get('title', ''),
                    'department':      dept,
                    'sector':          classify_department(j.get('title', ''), dept),
                    'location':        j.get('location', ''),
                    'country':         loc['country'] or '',
                    'remote':          j.get('remote', False),
                    'employment_type': 'Full-time',
                    'description':     j.get('description', '')[:8000],
                    'url':             j.get('url', ''),
                    'posted_at':       j.get('created_at'),
                })
        print(f"  [Arbeitnow] {len(out)} jobs fetched")
    except Exception as e:
        print(f"  [Arbeitnow] Error: {e}")
    return out
