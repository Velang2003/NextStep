"""
Remotive API Service — https://remotive.com/api/remote-jobs
Free, no API key. Returns remote tech jobs globally.
"""
import requests
from .data_normalizer import classify_department, normalize_location

API_URL = "https://remotive.com/api/remote-jobs?limit=500"

CATEGORY_MAP = {
    'Software Development': 'Engineering',
    'DevOps / Sysadmin':    'Engineering',
    'Data':                 'Data & AI',
    'Design':               'Design',
    'Product':              'Product Management',
    'Marketing':            'Marketing',
    'Customer Service':     'Customer Success',
    'Finance / Legal':      'Finance & Accounting',
    'Human Resources':      'Human Resources',
    'QA':                   'Engineering',
    'Sales':                'Sales',
}

def fetch_all() -> list[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(API_URL, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"  [Remotive] HTTP {resp.status_code}")
            return []
        jobs_raw = resp.json().get('jobs', [])
        out = []
        for j in jobs_raw:
            cat  = j.get('category', '')
            loc  = normalize_location(j.get('candidate_required_location', 'Remote'))
            dept = CATEGORY_MAP.get(cat, cat or 'Other')
            out.append({
                'source':          'remotive',
                'source_id':       str(j.get('id', '')),
                'company':         j.get('company_name', ''),
                'title':           j.get('title', ''),
                'department':      dept,
                'sector':          classify_department(j.get('title', ''), dept),
                'location':        j.get('candidate_required_location', 'Remote'),
                'country':         loc['country'] or 'Remote',
                'remote':          True,
                'employment_type': j.get('job_type', 'Full-time'),
                'description':     j.get('description', '')[:8000],
                'url':             j.get('url', ''),
                'posted_at':       j.get('publication_date'),
            })
        print(f"  [Remotive] {len(out)} jobs fetched")
        return out
    except Exception as e:
        print(f"  [Remotive] Error: {e}")
        return []
