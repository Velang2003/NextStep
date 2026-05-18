from app import db
from app.models.job import JobListing
from app.models.job_skill import JobSkill
from app.models.taxonomy import RoleTaxonomy, RoleSkill, SkillTaxonomy
from sqlalchemy import func
import time
import threading

_intel_cache = {}
_cache_lock = threading.RLock()
_CACHE_TTL = 3600  # 1 hour

# Words that by themselves are not meaningful role identifiers
_STOP_WORDS = {'developer', 'engineer', 'senior', 'junior', 'lead', 'staff', 'manager',
               'specialist', 'chief', 'officer', 'director', 'head', 'principal', 'associate'}

def invalidate_role_cache(role_name: str):
    """Force cache refresh for a role — call this when a user's target_role changes."""
    if role_name:
        with _cache_lock:
            _intel_cache.pop(role_name, None)

def get_role_intelligence(role_name: str) -> dict:
    """
    Returns unified intelligence data for a role, combining market demand and taxonomy standards.
    Returns: {
        'role_id': int,
        'canonical_title': str,
        'demand_data': { skill_name: { 'count': int, 'percentage': float, 'source': str } },
        'total_jobs': int
    }
    """
    from app.services.data_normalizer import normalize_role
    
    # Check cache (thread-safe read)
    now = time.time()
    with _cache_lock:
        cached = _intel_cache.get(role_name)
    if cached and (now - cached['timestamp']) < _CACHE_TTL:
        return cached['data']

    # 1. Normalize Role
    canonical_title = normalize_role(role_name)
    role_obj = RoleTaxonomy.query.filter_by(title=canonical_title).first()
    role_id = role_obj.id if role_obj else None

    # 2. Fetch Market Demand (JobListings by role_id or title)
    # Refinement: If we have a role_id, use its sector for strict filtering to avoid 'unnatural' noise
    sector_id = role_obj.sector_id if role_obj else None
    
    query_specific = db.session.query(JobListing.id).filter(JobListing.status == 'active')
    if role_id:
        query_specific = query_specific.filter(JobListing.role_id == role_id)
    else:
        query_specific = query_specific.filter(JobListing.title.ilike(f"%{role_name}%"))
        
    if sector_id:
        query_specific = query_specific.filter(JobListing.sector_id == sector_id)
    
    specific_job_ids = [r[0] for r in query_specific.limit(200).all()]
    final_job_ids = specific_job_ids
    
    # Smart Aggregation: If data is sparse (<30 jobs), broaden to title keyword matching
    if len(specific_job_ids) < 30 and role_name:
        words = [k for k in role_name.split() if k.lower() not in _STOP_WORDS]
        main_kw = words[-1] if words else role_name
        if not words or len(main_kw) <= 3:
            main_kw = role_name
        
        broad_query = db.session.query(JobListing.id).filter(
            JobListing.title.ilike(f"%{main_kw}%"),
            JobListing.status == 'active',
            ~JobListing.id.in_(specific_job_ids)
        )
        if sector_id:
            broad_query = broad_query.filter(JobListing.sector_id == sector_id)
            
        broad_query_ids = [r[0] for r in broad_query.limit(300 - len(specific_job_ids)).all()]
        final_job_ids.extend(broad_query_ids)

    total_jobs = len(final_job_ids)

    market_skills = {}
    if final_job_ids:
        demand_rows = db.session.query(
            SkillTaxonomy.canonical_name,
            func.count(JobSkill.id).label('cnt')
        ).join(JobSkill, JobSkill.skill_id == SkillTaxonomy.id)\
         .filter(JobSkill.job_id.in_(final_job_ids))\
         .group_by(SkillTaxonomy.canonical_name).all()
        
        for name, count in demand_rows:
            market_skills[name] = {
                'count': count,
                'percentage': round((count / total_jobs) * 100, 1) if total_jobs > 0 else 0
            }

    # 3. Fetch Taxonomy Requirements (RoleSkill)
    taxonomy_skills = set()
    if role_id:
        ts_rows = db.session.query(SkillTaxonomy.canonical_name).join(
            RoleSkill, RoleSkill.skill_id == SkillTaxonomy.id
        ).filter(RoleSkill.role_id == role_id).all()
        taxonomy_skills = {r[0] for r in ts_rows}

    # 4. Unified Merge Logic (Dynamic Market/Taxonomy Weighting)
    # High data volume (50+ jobs) -> Trust Market (80/20 split)
    # Low data volume (<10 jobs)  -> Trust Taxonomy (30/70 split)
    if total_jobs >= 50:
        m_weight, t_weight = 0.8, 20.0
    elif total_jobs >= 20:
        m_weight, t_weight = 0.6, 40.0
    else:
        m_weight, t_weight = 0.3, 70.0

    skill_categories = {s.canonical_name: s.category for s in SkillTaxonomy.query.with_entities(SkillTaxonomy.canonical_name, SkillTaxonomy.category).all()}
    expected_categories = set()
    if role_id:
        ec_rows = db.session.query(SkillTaxonomy.category).join(
            RoleSkill, RoleSkill.skill_id == SkillTaxonomy.id
        ).filter(RoleSkill.role_id == role_id).distinct().all()
        expected_categories = {r[0] for r in ec_rows}

    unified_demand = {}
    all_skill_names = set(market_skills.keys()) | taxonomy_skills
    
    for sname in all_skill_names:
        market_info = market_skills.get(sname, {'count': 0, 'percentage': 0.0})
        in_taxonomy = sname in taxonomy_skills
        scategory = skill_categories.get(sname)
        
        # Calculate Weighted Score
        market_score = market_info['percentage'] * m_weight
        taxo_score = t_weight if in_taxonomy else 0.0
        
        # --- NOISE PENALTY ---
        # If the skill category is NOT expected for this role, we penalize the market score heavily
        # to filter out 'unnatural' cross-sector noise (e.g. 'Excel' for 'Backend Developer')
        if expected_categories and scategory not in expected_categories:
            if market_info['percentage'] < 25: # Trust market only if absolutely dominant
                market_score *= 0.05 # 95% penalty for noise
        
        combined_pct = round(market_score + taxo_score, 1)
        
        # If no jobs found at all, but in taxonomy, we treat it as 100% "required by standard"
        if total_jobs == 0 and in_taxonomy:
            combined_pct = 100.0

        unified_demand[sname] = {
            'skill': sname,
            'demand_percentage': combined_pct,
            'market_count': market_info['count'],
            'is_standard': in_taxonomy,
            'category': scategory
        }

    result = {
        'role_id': role_id,
        'canonical_title': canonical_title,
        'demand_data': unified_demand,
        'total_jobs_analyzed': total_jobs
    }
    
    # Store in cache (thread-safe write)
    with _cache_lock:
        _intel_cache[role_name] = {'timestamp': now, 'data': result}
    
    return result
