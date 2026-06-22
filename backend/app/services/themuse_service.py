"""
The Muse API Service — https://www.themuse.com/api/public/jobs
Free tier, no API key for basic access. Returns up to 5000 jobs across 20 pages.
"""
import requests
from .data_normalizer import classify_department, normalize_location

API_URL  = "https://www.themuse.com/api/public/jobs"
MAX_PAGES = 20
PER_PAGE  = 100

def fetch_all() -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    out = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def _fetch_page(page):
        page_jobs = []
        try:
            resp = requests.get(API_URL, params={'page': page, 'per_page': PER_PAGE}, headers=headers, timeout=15)
            if resp.status_code == 200:
                data  = resp.json()
                jobs  = data.get('results', [])
                for j in jobs:
                    cats   = j.get('categories', [])
                    dept   = cats[0].get('name', '') if cats else ''
                    locs   = j.get('locations', [])
                    loc_str= locs[0].get('name', '') if locs else ''
                    loc    = normalize_location(loc_str)
                    levels = j.get('levels', [])
                    seniority = levels[0].get('name', '') if levels else ''
                    title  = j.get('name', '')
                    co     = j.get('company', {}).get('name', '')
                    page_jobs.append({
                        'source':          'themuse',
                        'source_id':       str(j.get('id', '')),
                        'company':         co,
                        'title':           f"{seniority} {title}".strip() if seniority else title,
                        'department':      dept,
                        'sector':          classify_department(title, dept),
                        'location':        loc_str,
                        'country':         loc['country'] or '',
                        'remote':          'remote' in loc_str.lower(),
                        'employment_type': 'Full-time',
                        'description':     j.get('contents', '')[:8000],
                        'url':             j.get('refs', {}).get('landing_page', ''),
                        'posted_at':       j.get('publication_date'),
                    })
        except Exception:
            pass
        return page_jobs

    try:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(_fetch_page, page) for page in range(1, MAX_PAGES + 1)]
            for fut in as_completed(futures, timeout=120):
                out.extend(fut.result())
        print(f"  [The Muse] {len(out)} jobs fetched")
    except Exception as e:
        print(f"  [The Muse] Error: {e}")
    return out
