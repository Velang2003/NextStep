from flask import Blueprint, request, jsonify
from app.utils.auth_helpers import firebase_required, admin_required
from app.services.pipeline import (
    run_pipeline, get_skill_trends, get_job_listings,
    get_role_trends, get_sector_trends
)

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/sync', methods=['POST'])
@firebase_required
@admin_required
def sync_jobs():
    """Trigger a full ATS data pipeline sync. Admin-only endpoint."""
    try:
        result = run_pipeline()
        return jsonify({'message': 'Sync complete.', 'result': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/', methods=['GET'])
def list_jobs():
    """
    Paginated job listings.
    Query params: country, remote, sector, skill, search, page, per_page
    """
    filters = {
        'country': request.args.get('country'),
        'remote':  request.args.get('remote', '').lower() == 'true' if request.args.get('remote') else None,
        'sector':  request.args.get('sector'),
        'skill':   request.args.get('skill'),
        'search':  request.args.get('search'),
    }
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    return jsonify(get_job_listings(filters=filters, page=page, per_page=per_page)), 200


@jobs_bp.route('/trends/skills', methods=['GET'])
def skill_trends():
    """Top skill demands. Query params: sector (optional), limit (default 20)"""
    sector = request.args.get('sector')
    limit  = int(request.args.get('limit', 20))
    return jsonify(get_skill_trends(sector=sector, limit=limit)), 200


@jobs_bp.route('/trends/role-skills', methods=['GET'])
def role_skills():
    """Get high-demand skills for a specific role using unified intelligence service."""
    role = request.args.get('role')
    if not role:
        return jsonify([]), 200

    from app.services.intelligence_service import get_role_intelligence
    intel = get_role_intelligence(role)
    demand_data = intel['demand_data']

    # Sort by demand percentage and take top 15
    sorted_skills = sorted(demand_data.keys(), key=lambda s: demand_data[s]['demand_percentage'], reverse=True)[:15]
    return jsonify(sorted_skills), 200



@jobs_bp.route('/trends/roles', methods=['GET'])
def role_trends():
    """Top roles by demand, filterable by sector."""
    sector = request.args.get('sector')
    limit  = int(request.args.get('limit', 20))
    return jsonify(get_role_trends(sector=sector, limit=limit)), 200


@jobs_bp.route('/trends/sectors', methods=['GET'])
def sector_breakdown():
    """Sectors with job counts and growth percentages."""
    return jsonify(get_sector_trends()), 200


@jobs_bp.route('/trends/locations', methods=['GET'])
def location_breakdown():
    """Distribution of job listings by country."""
    from app.models.job import JobListing, db
    from sqlalchemy import func
    rows = db.session.query(
        JobListing.country, func.count(JobListing.id).label('count')
    ).filter(
        JobListing.country != '',
        JobListing.status == 'active'
    ).group_by(JobListing.country).order_by(
        func.count(JobListing.id).desc()
    ).limit(30).all()
    return jsonify([{'country': r[0], 'count': r[1]} for r in rows]), 200


@jobs_bp.route('/trends/geo', methods=['GET'])
def geo_data():
    """Job counts by country with ISO3 codes and coordinates for map visualization."""
    from app.models.job import JobListing, db
    from app.models.taxonomy import CountryMapping, SkillTaxonomy
    from app.models.job_skill import JobSkill
    from sqlalchemy import func

    rows = db.session.query(
        JobListing.country, func.count(JobListing.id).label('count')
    ).filter(
        JobListing.country != '',
        JobListing.status == 'active'
    ).group_by(JobListing.country).order_by(
        func.count(JobListing.id).desc()
    ).all()

    country_map = {c.country_name: c for c in CountryMapping.query.all()}

    # Pre-aggregate ALL dominants in 3 bulk queries
    from sqlalchemy import over, desc as sa_desc
    from sqlalchemy.orm import aliased

    # Simple approach: pre-fetch per-country top values in 3 optimized subqueries
    country_names = [r[0] for r in rows]

    # Top role per country
    role_sub = db.session.query(
        JobListing.country,
        JobListing.title,
        func.count(JobListing.id).label('cnt')
    ).filter(
        JobListing.country.in_(country_names),
        JobListing.status == 'active'
    ).group_by(JobListing.country, JobListing.title).subquery()
    
    top_roles = {}
    for country, title, _ in db.session.query(role_sub.c.country, role_sub.c.title, role_sub.c.cnt).all():
        if country not in top_roles:
            top_roles[country] = title

    # Top skill per country
    skill_sub = db.session.query(
        JobListing.country,
        SkillTaxonomy.canonical_name,
        func.count(JobSkill.id).label('cnt')
    ).join(JobSkill, JobSkill.job_id == JobListing.id)\
     .join(SkillTaxonomy, SkillTaxonomy.id == JobSkill.skill_id)\
     .filter(
         JobListing.country.in_(country_names),
         JobListing.status == 'active'
     )\
     .group_by(JobListing.country, SkillTaxonomy.canonical_name)\
     .order_by(JobListing.country, func.count(JobSkill.id).desc()).all()
    
    top_skills = {}
    for country, skill, _ in skill_sub:
        if country not in top_skills:
            top_skills[country] = skill

    # Top sector per country
    sector_sub = db.session.query(
        JobListing.country,
        JobListing.department,
        func.count(JobListing.id).label('cnt')
    ).filter(
        JobListing.country.in_(country_names), 
        JobListing.department.isnot(None),
        JobListing.status == 'active'
    )\
     .group_by(JobListing.country, JobListing.department)\
     .order_by(JobListing.country, func.count(JobListing.id).desc()).all()
    
    top_sectors = {}
    for country, sector, _ in sector_sub:
        if country not in top_sectors:
            top_sectors[country] = sector

    result = []
    for country_name, count in rows:
        entry = {
            'country': country_name,
            'count': count,
            'iso3': '',
            'lat': None,
            'lng': None,
            'dominant_role':   top_roles.get(country_name, 'N/A'),
            'dominant_skill':  top_skills.get(country_name, 'N/A'),
            'dominant_sector': top_sectors.get(country_name, 'N/A'),
        }
        cm = country_map.get(country_name)
        if cm:
            entry['iso3'] = cm.iso3
            entry['lat']  = cm.lat
            entry['lng']  = cm.lng
        result.append(entry)

    return jsonify(result), 200


@jobs_bp.route('/trends/skills/history', methods=['GET'])
def skill_trend_history():
    """Skill demand across multiple periods for time-series visualization."""
    from app.models.job import SkillTrend
    skill = request.args.get('skill')
    limit = int(request.args.get('limit', 10))

    if skill:
        trends = SkillTrend.query.filter_by(skill=skill).order_by(
            SkillTrend.period.asc()
        ).all()
        return jsonify([t.to_dict() for t in trends]), 200
    else:
        # Top skills with their period data
        from app import db
        from sqlalchemy import func
        top_skills = db.session.query(
            SkillTrend.skill
        ).group_by(SkillTrend.skill).order_by(
            func.sum(SkillTrend.count).desc()
        ).limit(limit).all()

        result = {}
        for (sk,) in top_skills:
            trends = SkillTrend.query.filter_by(skill=sk).order_by(
                SkillTrend.period.asc()
            ).all()
            result[sk] = [t.to_dict() for t in trends]

        return jsonify(result), 200


@jobs_bp.route('/dashboard-stats', methods=['GET'])
@firebase_required
def dashboard_stats():
    """Aggregated stats for the dashboard cards using relational logic."""
    from flask import g
    from app.models.user import User
    from app.models.job import JobListing
    from app.models.application import JobApplication
    from app.models.assessment import Assessment
    from app.models.taxonomy import SkillTaxonomy
    from app.models.job_skill import JobSkill
    from app import db
    from sqlalchemy import func

    user_id = g.user_id
    user = db.session.get(User, user_id)

    stats = {
        'skill_match': 0,
        'jobs_tracked': JobListing.query.filter_by(status='active').count(),
        'skills_gap': 0,
        'assessment_score': 0,
        'applications': 0,
    }

    if user and user.profile:
        profile = user.profile
        user_skills = {ps.skill.canonical_name for ps in profile.skills if not ps.is_desired and ps.skill}
        target_role = profile.target_role or ''

        if target_role:
            # Bug Fix #4: Use unified intelligence service for accurate, consistent Skill Match %
            from app.services.intelligence_service import get_role_intelligence
            intel = get_role_intelligence(target_role)
            demand_data = intel['demand_data']
            
            # Use Top 20 skills as denominator (mirrors get_skill_gap logic)
            top_skills = sorted(demand_data.keys(), key=lambda x: demand_data[x]['demand_percentage'], reverse=True)[:20]
            top_skill_names = set(top_skills)
            owned = user_skills & top_skill_names
            missing = top_skill_names - user_skills
            stats['skill_match'] = round(len(owned) / len(top_skill_names) * 100, 1) if top_skill_names else 0
            stats['skills_gap'] = len(missing)

        # Best assessment score
        best = Assessment.query.filter_by(user_id=user_id).order_by(
            Assessment.percentage.desc()
        ).first()
        if best:
            stats['assessment_score'] = best.percentage

        # Application count
        stats['applications'] = JobApplication.query.filter_by(user_id=user_id).count()

    return jsonify(stats), 200
