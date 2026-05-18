from app import db
from app.models.job import JobListing
from app.models.user import Profile

def calculate_skill_gap(profile_id: int, job_id: int) -> dict:
    profile = db.session.get(Profile, profile_id)
    job = db.session.get(JobListing, job_id)
    
    if not profile or not job:
        return {'error': 'Profile or Job not found'}
        
    known_skills = {ps.skill.canonical_name for ps in profile.skills if not ps.is_desired and ps.skill}
    required_skills = {js.skill.canonical_name for js in job.job_skills if js.skill}
    
    gap_skills = required_skills - known_skills
    match_skills = required_skills & known_skills
    
    # Cosine Similarity Calculation
    # 1. Create a unified vocabulary of all unique skills
    vocab = list(known_skills | required_skills)
    
    if not vocab:
        match_percentage = 100.0 if not required_skills else 0.0
    else:
        # 2. Build binary vectors for profile and job based on the vocabulary
        profile_vector = [1 if skill in known_skills else 0 for skill in vocab]
        job_vector = [1 if skill in required_skills else 0 for skill in vocab]
        
        # 3. Calculate dot product and magnitudes
        import math
        dot_product = sum(p * j for p, j in zip(profile_vector, job_vector))
        mag_profile = math.sqrt(sum(p * p for p in profile_vector))
        mag_job = math.sqrt(sum(j * j for j in job_vector))
        
        # 4. Compute similarity score
        if mag_profile == 0 or mag_job == 0:
            similarity = 0.0
        else:
            similarity = dot_product / (mag_profile * mag_job)
            
        match_percentage = round(similarity * 100, 1)
    
    return {
        'required': list(required_skills),
        'known': list(known_skills),
        'gap': list(gap_skills),
        'match': list(match_skills),
        'match_percentage': match_percentage
    }

def get_course_recommendations(skill_name: str, limit: int = 3) -> list:
    """Uses duckduckgo-search to find free courses for a given skill on youtube or coursera"""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            # specifically search for tutorials
            query = f"site:youtube.com OR site:coursera.org {skill_name} full course tutorial"
            search_results = ddgs.text(query, max_results=limit)
            
            for r in search_results:
                results.append({
                    'title': r.get('title'),
                    'url': r.get('href'),
                    'snippet': r.get('body')
                })
        return results
    except Exception as e:
        print(f"Error fetching courses for {skill_name}: {e}")
        return []
