from flask import request, jsonify, g
from app import db
from app.models.user import User, Profile, ProfileSkill
from app.models.job import JobListing, SkillTrend
from app.models.taxonomy import SkillTaxonomy, RoleTaxonomy, RoleSkill
from app.models.job_skill import JobSkill
from app.services.intelligence_service import get_role_intelligence, invalidate_role_cache
from app.services.cache_service import cached, cache_svc
from sqlalchemy import func


def update_profile():
    user_id = g.user_id
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    data = request.get_json()
    profile = user.profile or Profile(user_id=user_id)

    # Capture old target_role before updating (for cache invalidation)
    old_target_role = profile.target_role

    profile.first_name       = data.get('first_name', profile.first_name)
    profile.last_name        = data.get('last_name', profile.last_name)
    profile.current_role     = data.get('current_role', profile.current_role)
    profile.target_role      = data.get('target_role', profile.target_role)
    profile.location         = data.get('location', profile.location)
    try:
        profile.experience_years = int(data.get('experience_years', profile.experience_years or 0))
    except (ValueError, TypeError):
        pass

    # Bug Fix #1: Invalidate intelligence cache when target role changes
    new_target_role = profile.target_role
    if old_target_role != new_target_role:
        invalidate_role_cache(old_target_role)
        invalidate_role_cache(new_target_role)

    # Synchronize ProfileSkills
    def sync_skills(skill_names, is_desired):
        if skill_names is None:
            return
        
        if isinstance(skill_names, str):
            skill_names = [s.strip() for s in skill_names.split(',') if s.strip()]
        
        # Get existing skills of this type for the user
        existing_links = ProfileSkill.query.filter_by(profile_id=profile.id, is_desired=is_desired).all()
        existing_map = {link.skill.canonical_name: link for link in existing_links if link.skill}
        
        new_names = set(skill_names)
        
        # Remove skills not in the new list
        for name, link in existing_map.items():
            if name not in new_names:
                db.session.delete(link)
        
        # Add new skills
        for name in new_names:
            if name not in existing_map:
                # Find skill in taxonomy
                skill_obj = SkillTaxonomy.query.filter_by(canonical_name=name).first()
                if not skill_obj:
                    # Create unapproved skill if missing
                    skill_obj = SkillTaxonomy(canonical_name=name, is_approved=False, category='Uncategorized')
                    db.session.add(skill_obj)
                    db.session.flush()
                
                new_link = ProfileSkill(profile_id=profile.id, skill_id=skill_obj.id, is_desired=is_desired)
                db.session.add(new_link)

    # Ensure profile is persisted (and has an ID) before syncing skills
    if not user.profile:
        db.session.add(profile)
        db.session.flush()  # Get profile ID for foreign-key links

    sync_skills(data.get('skills'), is_desired=False)
    sync_skills(data.get('desired_skills'), is_desired=True)

    db.session.commit()

    # Invalidate User Cache
    cache_svc.clear_pattern(f"user:{user_id}:*")

    return jsonify({'message': 'Profile updated.', 'profile': profile.to_dict()}), 200


@cached("user:{g.user_id}:skill_gap", timeout=3600)
def get_skill_gap():
    """
    Compare user's current skills vs skills demanded in jobs matching their target role.
    Uses Weighted Cosine Similarity for precision.
    """
    user_id = g.user_id
    user = db.session.get(User, user_id)
    if not user or not user.profile:
        return jsonify({'error': 'Complete your profile first.'}), 400

    profile = user.profile
    user_skills = {ps.skill.canonical_name for ps in profile.skills if not ps.is_desired and ps.skill}
    target_role = profile.target_role

    if not target_role:
        return jsonify({'error': 'Add a target role to your profile.'}), 400

    # Fetch unified intelligence data (contains TF-IDF weighted demand)
    intel = get_role_intelligence(target_role)
    demand_data = intel['demand_data']
    
    if not demand_data:
        return jsonify({'match_percentage': 0, 'owned_skills': [], 'missing_skills': [], 'jobs_analyzed': 0}), 200

    # Fetch User's Best Assessment Scores EARLY so they can impact the Match Score
    from app.models.assessment import Assessment
    assessments = Assessment.query.filter_by(user_id=user_id).all()
    best_scores = {}
    for a in assessments:
        if a.skill:
            sname = a.skill.canonical_name
            if sname not in best_scores or a.percentage > best_scores[sname]:
                best_scores[sname] = a.percentage

    # --- Weighted Cosine Similarity ---
    # 1. Vocabulary: Top 100 skills by demand (expanded from 30 for more 'natural' depth)
    vocab = sorted(demand_data.keys(), key=lambda x: demand_data[x]['demand_percentage'], reverse=True)[:100]
    
    import math
    dot_product = 0.0
    mag_user = 0.0
    mag_role = 0.0
    
    for sname in vocab:
        role_weight = demand_data[sname]['demand_percentage'] / 100.0
        
        # User Weight Calculation: 
        # - Not owned: 0
        # - Owned but no test: 0.8 (baseline)
        # - Tested: percentage/100 * 1.2 (reward proven mastery up to 1.2x)
        user_weight = 0.0
        if sname in user_skills:
            score = best_scores.get(sname)
            if score is not None:
                user_weight = (score / 100.0) * 1.2
            else:
                user_weight = 0.8 # Baseline weight for unchecked skills
        
        dot_product += (user_weight * role_weight)
        mag_user += (user_weight ** 2)
        mag_role += (role_weight ** 2)
    
    mag_user = math.sqrt(mag_user)
    mag_role = math.sqrt(mag_role)
    
    if mag_user == 0 or mag_role == 0:
        match_pct = 0.0
    else:
        # Standard cosine similarity
        similarity = dot_product / (mag_user * mag_role)
        # Boost and Cap: Make the score feel more 'natural' (people find low percentages discouraging)
        match_pct = min(100.0, round(similarity * 110, 1)) 

    # Compute missing skills: skills in demand that the user does NOT have
    missing = [s for s in demand_data.keys() if s not in user_skills]

    # Return as a list of dictionaries for radar chart support
    results = []
    top_skills_list = sorted(demand_data.keys(), key=lambda k: demand_data[k]['demand_percentage'], reverse=True)[:15]
    top_skills_set = set(top_skills_list)
    
    for skill_name, data in demand_data.items():
        if skill_name in top_skills_set:
            # User Level: Assessment score if exists, else 100 if they have the skill, else 0
            u_score = best_scores.get(skill_name)
            if u_score is None:
                u_score = 100.0 if skill_name in user_skills else 0.0
            
            results.append({
                'skill': skill_name,
                'demand_percentage': data['demand_percentage'], # Base Layer: Market Demand
                'user_score': u_score,                           # Top Layer: User Strength
                'is_standard': data['is_standard']
            })
    
    # Build demand_frequencies map for the frontend radar chart
    demand_frequencies = {}
    for skill_name, d in demand_data.items():
        demand_frequencies[skill_name] = d['demand_percentage']

    owned_skills_list = sorted(
        [s for s in user_skills if s in demand_data],
        key=lambda s: demand_data.get(s, {}).get('demand_percentage', 0),
        reverse=True
    )

    return jsonify({
        'target_role': target_role,
        'role': target_role,
        'match_percentage': match_pct,
        'skill_gap': results,
        'owned_skills': owned_skills_list,
        'missing_skills': sorted(missing, key=lambda s: demand_data.get(s, {}).get('demand_percentage', 0), reverse=True)[:15],
        'demand_frequencies': demand_frequencies,
        'jobs_analyzed': intel.get('total_jobs_analyzed', 0),
    }), 200


@cached("user:{g.user_id}:career_path", timeout=3600)
def get_career_path():
    """
    Recommend learning path based on missing skills sorted by market demand for the target role.
    Uses unified intelligence_service for precision.
    """
    user_id = g.user_id
    user = db.session.get(User, user_id)
    if not user or not user.profile:
        return jsonify({'error': 'Complete your profile first.'}), 400

    profile = user.profile
    user_skills = {ps.skill.canonical_name for ps in profile.skills if not ps.is_desired and ps.skill}
    target_role = profile.target_role

    if not target_role:
        return jsonify({'error': 'Add a target role to your profile.'}), 400

    # Fetch unified intelligence
    intel = get_role_intelligence(target_role)
    demand_data = intel['demand_data']

    # Fetch User's Best Assessment Scores
    from app.models.assessment import Assessment
    assessments = Assessment.query.filter_by(user_id=user_id).all()
    all_best_scores = {a.skill.canonical_name: a.percentage for a in assessments if a.skill}

    # Bug Fix #6: Only show assessment results for skills RELEVANT to the target role
    relevant_skill_names = set(demand_data.keys())
    best_scores = {k: v for k, v in all_best_scores.items() if k in relevant_skill_names}

    strong_skills = []
    improvement_skills = []
    for skill_name, score in best_scores.items():
        if score >= 70:
            strong_skills.append({'skill': skill_name, 'score': score})
        else:
            improvement_skills.append({'skill': skill_name, 'score': score})

    strong_skill_names = set(s['skill'] for s in strong_skills)
    
    # Tiering logic based on unified demand percentage
    tiers = {'critical': [], 'important': [], 'nice_to_have': []}
    
    missing_skills = [s for s in demand_data.keys() if s not in user_skills and s not in strong_skill_names]
    sorted_missing = sorted(missing_skills, key=lambda s: demand_data[s]['demand_percentage'], reverse=True)[:25]
    
    for sname in sorted_missing:
        info = demand_data[sname]
        pct = info['demand_percentage']
        # Bug Fix #8: Include market_count in item so frontend can display it
        item = {
            'skill': sname,
            'demand_pct': pct,
            'is_standard': info['is_standard'],
            'market_count': info.get('market_count', 0)
        }
        
        # Adjusting Tier Thresholds for a more 'natural' feel. 
        # In fragmented markets, 45% is already very critical.
        if pct >= 45:
            tiers['critical'].append(item)
        elif pct >= 15:
            tiers['important'].append(item)
        else:
            tiers['nice_to_have'].append(item)

    return jsonify({
        'target_role':   profile.target_role,
        'canonical_role': intel['canonical_title'],
        'learning_path': tiers,
        'strong_skills': strong_skills,
        'improvement_skills': improvement_skills,
        'jobs_analyzed': intel['total_jobs_analyzed'],
    }), 200


@cached("user:{g.user_id}:recommended_roles", timeout=3600)
def get_recommended_roles():
    """
    NEW: Recommend top in-demand job roles based on the user's current skills.
    For each role in the taxonomy, calculate how many of the user's skills
    are in that role's required skill set, and score by role market demand.
    """
    user_id = g.user_id
    user = db.session.get(User, user_id)
    if not user or not user.profile:
        return jsonify({'error': 'Complete your profile first.'}), 400

    profile = user.profile
    user_skill_ids = {ps.skill_id for ps in profile.skills if not ps.is_desired and ps.skill}
    user_skill_names = {ps.skill.canonical_name for ps in profile.skills if not ps.is_desired and ps.skill}

    if not user_skill_ids:
        return jsonify({'error': 'Add some skills to your profile to get recommendations.'}), 400

    # Fetch User's Best Assessment Scores
    from app.models.assessment import Assessment
    assessments = Assessment.query.filter_by(user_id=user_id).all()
    best_scores = {a.skill.canonical_name: a.percentage for a in assessments if a.skill}

    # Fetch all roles with their skill requirements
    all_roles = RoleTaxonomy.query.all()
    
    # Count live jobs per role for market demand scoring
    job_counts = dict(
        db.session.query(JobListing.role_id, func.count(JobListing.id))
        .filter(JobListing.role_id.isnot(None), JobListing.status == 'active')
        .group_by(JobListing.role_id)
        .all()
    )

    results = []
    current_target = profile.target_role or ''

    for role in all_roles:
        # Get required skills for this role
        role_skills = [rs.skill for rs in role.role_skills if rs.skill]
        if not role_skills:
            continue

        # Calculate weighted skill match based on assessments
        total_points = 0.0
        matched_names = []
        
        for skill in role_skills:
            sname = skill.canonical_name
            if sname in user_skill_names:
                matched_names.append(sname)
                # Weighted Point System:
                # - Tested & Expert (>80): 1.2 pts
                # - Tested & Competent: score/100 * 1.1 pts
                # - Untested: 0.8 pts (baseline)
                score = best_scores.get(sname)
                if score is not None:
                    total_points += min(1.2, (score / 100.0) * 1.1)
                else:
                    total_points += 0.8
        
        # match_pct = (points / required_count) * 100
        match_pct = min(100.0, round((total_points / len(role_skills)) * 100, 1))

        # Merge with market demand (open job count)
        live_jobs = job_counts.get(role.id, 0)

        # Composite score: 60% skill match + 40% market demand
        demand_score = min(live_jobs / 500, 1.0) * 40
        composite = round(match_pct * 0.6 + demand_score, 1)

        results.append({
            'role': role.title,
            'match_percentage': match_pct,
            'composite_score': composite,
            'live_jobs': live_jobs,
            'matched_skills': matched_names[:5],
            'total_required': len(role_skills),
            'is_current_target': role.title.lower() == current_target.lower()
        })

    # Sort by composite score and return top 10, excluding current target role
    results.sort(key=lambda r: r['composite_score'], reverse=True)
    # Put current target first if present, then show other recommendations
    target_match = [r for r in results if r['is_current_target']]
    others = [r for r in results if not r['is_current_target']][:9]

    return jsonify({
        'current_target': current_target,
        'user_skills': sorted(user_skill_names),
        'recommended_roles': target_match + others
    }), 200
