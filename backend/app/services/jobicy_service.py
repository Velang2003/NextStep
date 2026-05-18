"""
Jobicy API Service — https://jobicy.com/api/v2/remote-jobs
Free, no API key. Returns remote jobs globally, paginates up to 5 pages.
"""
import requests
from .data_normalizer import classify_department, normalize_location

API_URL   = "https://jobicy.com/api/v2/remote-jobs"
MAX_PAGES = 5

def fetch_all() -> list[dict]:
    out = []
    try:
        for page in range(1, MAX_PAGES + 1):
            resp = requests.get(API_URL, params={'count': 50, 'offset': (page-1)*50}, timeout=15)
            if resp.status_code != 200:
                break
            jobs = resp.json().get('jobs', [])
            if not jobs:
                break
            for j in jobs:
                industry = j.get('jobIndustry', '')
                loc_str  = j.get('jobGeo', 'Remote')
                loc      = normalize_location(loc_str)
                out.append({
                    'source':          'jobicy',
                    'source_id':       str(j.get('id', '')),
                    'company':         j.get('companyName', ''),
                    'title':           j.get('jobTitle', ''),
                    'department':      industry,
                    'sector':          classify_department(j.get('jobTitle', ''), industry),
                    'location':        loc_str,
                    'country':         loc['country'] or 'Remote',
                    'remote':          True,
                    'employment_type': j.get('jobType', 'Full-time'),
                    'description':     j.get('jobDescription', '')[:8000],
                    'url':             j.get('url', ''),
                    'posted_at':       j.get('pubDate'),
                })
        print(f"  [Jobicy] {len(out)} jobs fetched")
    except Exception as e:
        print(f"  [Jobicy] Error: {e}")
    return out
