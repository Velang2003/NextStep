"""
Taxonomy API routes — serve skills, sectors, roles from the database.
"""
from flask import Blueprint, request, jsonify
from app.models.taxonomy import SkillTaxonomy, SectorTaxonomy, RoleTaxonomy

taxonomy_bp = Blueprint('taxonomy', __name__)


@taxonomy_bp.route('/skills', methods=['GET'])
def list_skills():
    """
    List all skills. Optional query params: category, search, page, per_page
    """
    category = request.args.get('category')
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))

    query = SkillTaxonomy.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(SkillTaxonomy.canonical_name.ilike(f'%{search}%'))

    query = query.order_by(SkillTaxonomy.category, SkillTaxonomy.canonical_name)

    if per_page > 0:
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'skills': [s.to_dict() for s in paginated.items],
            'total': paginated.total,
            'page': page,
            'pages': paginated.pages,
        }), 200
    else:
        skills = query.all()
        return jsonify({'skills': [s.to_dict() for s in skills], 'total': len(skills)}), 200


@taxonomy_bp.route('/skills/categories', methods=['GET'])
def list_skill_categories():
    """List unique skill categories."""
    from app import db
    rows = db.session.query(SkillTaxonomy.category).distinct().order_by(
        SkillTaxonomy.category
    ).all()
    return jsonify([r[0] for r in rows]), 200


@taxonomy_bp.route('/sectors', methods=['GET'])
def list_sectors():
    """List all sectors."""
    sectors = SectorTaxonomy.query.order_by(SectorTaxonomy.name).all()
    return jsonify([s.to_dict() for s in sectors]), 200


@taxonomy_bp.route('/roles', methods=['GET'])
def list_roles():
    """List roles, optionally filtered by sector."""
    sector = request.args.get('sector')
    query = RoleTaxonomy.query
    if sector:
        from app.models.taxonomy import SectorTaxonomy as ST
        sec = ST.query.filter_by(name=sector).first()
        if sec:
            query = query.filter_by(sector_id=sec.id)
    roles = query.order_by(RoleTaxonomy.title).all()
    return jsonify([r.to_dict() for r in roles]), 200
