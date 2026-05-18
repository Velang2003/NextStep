from app import db

class JobSkill(db.Model):
    __tablename__ = 'job_skills'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_listings.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_taxonomy.id', ondelete='CASCADE'), nullable=False)
    proficiency_level = db.Column(db.String(50)) # e.g. beginner, intermediate, expert

    # We can add relationships here or backrefs in JobListing and SkillTaxonomy
    # Since we need to access skills from a job listing:
    skill = db.relationship('SkillTaxonomy')
