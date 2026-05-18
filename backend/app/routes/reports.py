from flask import Blueprint, send_file, jsonify, g
from app.utils.auth_helpers import firebase_required
from app import db
from app.models.user import User
from app.services.pipeline import get_skill_trends
from app.services.report_service import build_report
from app.models.assessment import Assessment
from app.models.application import JobApplication

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/download', methods=['GET'])
@firebase_required
def download_report():
    """Generate and stream a PDF career report for the current user."""
    user_id = g.user_id
    user    = db.session.get(User, user_id)

    if not user or not user.profile:
        return jsonify({'error': 'Complete your profile before generating a report.'}), 400

    try:
        from app.services.intelligence_service import get_role_intelligence
        from app.models.job import JobListing

        profile     = user.profile
        target_role = profile.target_role or ''
        # Use ORM relationship, not deprecated string field
        user_skills = {ps.skill.canonical_name for ps in profile.skills if not ps.is_desired and ps.skill}

        # --- Skill Gap (via unified Intelligence Engine) ---
        if target_role:
            intel       = get_role_intelligence(target_role)
            demand_data = intel['demand_data']

            top_skills        = sorted(demand_data.keys(), key=lambda x: demand_data[x]['demand_percentage'], reverse=True)[:20]
            top_skill_names   = set(top_skills)
            owned             = user_skills & top_skill_names
            missing           = [s for s in top_skills if s not in user_skills][:15]
            match_pct         = round(len(owned) / len(top_skill_names) * 100, 1) if top_skill_names else 0

            gap_data = {
                'match_percentage':   match_pct,
                'owned_skills':       sorted(owned),
                'missing_skills':     missing,
                'demand_frequencies': {s: demand_data[s]['demand_percentage'] for s in missing},
                'jobs_analyzed':      intel['total_jobs_analyzed'],
                'target_role':        target_role,
            }

            # --- Career Path (via unified Intelligence Engine) ---
            tiers = {'critical': [], 'important': [], 'nice_to_have': []}
            for sname in missing:
                info = demand_data[sname]
                pct  = info['demand_percentage']
                item = {'skill': sname, 'demand_pct': pct, 'market_count': info.get('market_count', 0)}
                if pct >= 60:
                    tiers['critical'].append(item)
                elif pct >= 25:
                    tiers['important'].append(item)
                else:
                    tiers['nice_to_have'].append(item)

            career_data = {
                'target_role':  target_role,
                'learning_path': tiers,
                'jobs_analyzed': intel['total_jobs_analyzed'],
            }
        else:
            gap_data    = {'match_percentage': 0, 'owned_skills': [], 'missing_skills': [],
                           'demand_frequencies': {}, 'jobs_analyzed': 0, 'target_role': ''}
            career_data = {'target_role': '', 'learning_path': {}, 'jobs_analyzed': 0}

        trend_data = get_skill_trends(limit=10)

        # --- Assessments (best score per skill) ---
        assessments = Assessment.query.filter_by(user_id=user.id).order_by(Assessment.taken_at.desc()).all()
        best_scores = {}
        for a in assessments:
            skill_name = a.skill.canonical_name if a.skill else 'Unknown'
            if skill_name not in best_scores or a.percentage > best_scores[skill_name]['percentage']:
                best_scores[skill_name] = a.to_dict()
        assessment_data = list(best_scores.values())

        # --- Applications ---
        apps     = JobApplication.query.filter_by(user_id=user.id).all()
        app_data = {
            'total':        len(apps),
            'saved':        sum(1 for a in apps if a.status == 'saved'),
            'applied':      sum(1 for a in apps if a.status == 'applied'),
            'interviewing': sum(1 for a in apps if a.status == 'interviewing'),
            'offered':      sum(1 for a in apps if a.status == 'offered'),
        }

    except Exception as e:
        return jsonify({'error': f'Error gathering report data: {str(e)}'}), 500

    pdf_buf = build_report(user, gap_data, career_data, trend_data, assessment_data, app_data)

    filename = f"nextstep_report_{user.email.split('@')[0]}.pdf"
    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )
