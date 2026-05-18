"""
Skill extraction and job data normalization utilities.
All taxonomy data is loaded from the database — nothing hardcoded.
"""
import re
import time
import threading

# In-memory cache with TTL to avoid hitting DB on every job parse
_cache = {
    'skills': None,      # { name: [ [token, token], ... ] }
    'sectors': None,
    'countries': None,
    'loaded_at': 0,
}
_cache_lock = threading.Lock()
_CACHE_TTL = 300  # seconds

_nlp = None


def discover_entities_spacy(text: str) -> dict:
    """Fallback discovery using Spacy NER and Noun Phrases."""
    if not _nlp or not text:
        return {'skills': [], 'roles': []}
    
    doc = _nlp(text[:2000])
    # Extract ORG, PRODUCT, and capitalized noun phrases as potential candidates
    skills = []
    roles = []
    
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
            skills.append(ent.text.strip())
            
    # Heuristic for roles: first few lines often contain title
    lines = text.split('\n')
    if lines:
        first_line = lines[0].strip()
        if len(first_line) > 5 and len(first_line) < 100:
            roles.append(first_line)
            
    return {
        'skills': list(set(skills)),
        'roles': list(set(roles))
    }


def _load_cache():
    """Load taxonomy data from DB into memory cache."""
    from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, CountryMapping, RoleTaxonomy
    with _cache_lock:
        now = time.time()
        if _cache.get('loaded_at') and (now - _cache['loaded_at']) < _CACHE_TTL:
            return

        # Load Skills with Aliases
        skills_rows = SkillTaxonomy.query.all()
        _cache['skills'] = {}
        for s in skills_rows:
            # Pre-tokenize all aliases to save time during extraction
            aliases = [a.name.lower() for a in s.aliases] + [s.canonical_name.lower()]
            if _nlp:
                _cache['skills'][s.canonical_name] = [
                    [t.text for t in _nlp(alias)] for alias in aliases
                ]
            else:
                _cache['skills'][s.canonical_name] = aliases

        # Load Sectors with Aliases
        sectors_rows = SectorTaxonomy.query.all()
        _cache['sectors'] = {
            s.name: [a.name.lower() for a in s.aliases] + [s.name.lower()]
            for s in sectors_rows
        }

        # Load Roles with Aliases
        roles_rows = RoleTaxonomy.query.all()
        _cache['roles'] = {
            r.title: [a.name.lower() for a in r.aliases] + [r.title.lower()]
            for r in roles_rows
        }

        countries_rows = CountryMapping.query.all()
        _cache['countries'] = []
        for c in countries_rows:
            _cache['countries'].append({
                'name': c.country_name,
                'iso3': c.iso3,
                'iso2': c.iso2,
                'aliases': [a.lower() for a in (c.aliases or [])],
                'lat': c.lat,
                'lng': c.lng,
            })

        _cache['loaded_at'] = now


def invalidate_cache():
    """Force a reload of taxonomy data on next access."""
    with _cache_lock:
        _cache['loaded_at'] = 0


def extract_skills(text: str) -> list[str]:
    """Return a deduplicated list of skills detected in `text` using pre-tokenized taxonomy aliases."""
    if not text:
        return []
    _load_cache()
    
    text_lower = text.lower()
    
    if not _nlp:
        # Fallback if spacy isn't installed
        found = []
        for skill_name, aliases in (_cache['skills'] or {}).items():
            for alias in aliases:
                if len(alias) <= 3:
                    if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                        found.append(skill_name)
                        break
                else:
                    if alias in text_lower:
                        found.append(skill_name)
                        break
        return list(dict.fromkeys(found))

    # Using pre-tokenized aliases for speed
    doc = _nlp(text_lower)
    tokens = [t.text for t in doc]
    clean_text_str = " " + " ".join(tokens) + " "
    
    found = []
    for skill_name, tokenized_aliases in (_cache['skills'] or {}).items():
        for t_alias in tokenized_aliases:
            # Create a string representation of tokens for efficient substring matching
            # while maintaining word boundaries
            clean_alias_str = " " + " ".join(t_alias) + " "
            if clean_alias_str in clean_text_str:
                found.append(skill_name)
                break
    return list(dict.fromkeys(found))


def classify_department(title: str, department: str) -> str:
    """Map a job title/department to a normalized sector label using DB taxonomy aliases."""
    _load_cache()
    text = f"{title} {department}".lower()
    best_match = 'Other'
    best_score = 0
    for sector_name, aliases in (_cache['sectors'] or {}).items():
        if sector_name == 'Other':
            continue
        # Count alias matches
        score = sum(1 for alias in aliases if alias in text)
        if score > best_score:
            best_score = score
            best_match = sector_name
    return best_match


def normalize_role(title: str) -> str:
    """Map a raw job title to a canonical Role title."""
    _load_cache()
    title_lower = title.lower()
    best_match = title # Fallback to original
    best_score = 0
    for canonical, aliases in (_cache['roles'] or {}).items():
        for alias in aliases:
            if alias in title_lower and len(alias) > best_score:
                best_score = len(alias)
                best_match = canonical
    return best_match


def normalize_location(location_str: str) -> dict:
    """Return {location, country, country_iso3, remote} from a raw location string."""
    if not location_str:
        return {'location': '', 'country': '', 'country_iso3': '', 'remote': False}

    _load_cache()
    loc = location_str.strip()
    remote = any(kw in loc.lower() for kw in ['remote', 'anywhere', 'distributed', 'work from home'])

    country = ''
    country_iso3 = ''
    loc_lower = loc.lower()
    best_match_len = 0

    for c in (_cache['countries'] or []):
        for alias in c['aliases']:
            if alias in loc_lower and len(alias) > best_match_len:
                country = c['name']
                country_iso3 = c['iso3']
                best_match_len = len(alias)

    return {
        'location': loc,
        'country': country,
        'country_iso3': country_iso3,
        'remote': remote,
    }
