from app import db
from datetime import datetime, timezone


class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))          # null for Google-only users
    google_id  = db.Column(db.String(120), unique=True, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':         self.id,
            'email':      self.email,
            'google_id':  self.google_id,
            'is_admin':   self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'profile':    self.profile.to_dict() if self.profile else None,
        }

    def __repr__(self):
        return f'<User {self.email}>'


class ProfileSkill(db.Model):
    __tablename__ = 'profile_skills'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_taxonomy.id', ondelete='CASCADE'), nullable=False)
    is_desired = db.Column(db.Boolean, default=False)
    
    skill = db.relationship('SkillTaxonomy')

class Profile(db.Model):
    __tablename__ = 'profiles'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name   = db.Column(db.String(50))
    last_name    = db.Column(db.String(50))
    current_role = db.Column(db.String(100))
    target_role  = db.Column(db.String(100))
    location     = db.Column(db.String(100))
    experience_years = db.Column(db.Integer, default=0)
    
    skills = db.relationship('ProfileSkill', backref='profile', cascade='all, delete-orphan')

    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        current_skills = [ps.skill.canonical_name for ps in self.skills if not ps.is_desired and ps.skill]
        desired_skills = [ps.skill.canonical_name for ps in self.skills if ps.is_desired and ps.skill]

        return {
            'first_name':       self.first_name,
            'last_name':        self.last_name,
            'current_role':     self.current_role,
            'target_role':      self.target_role,
            'location':         self.location,
            'experience_years': self.experience_years,
            'skills':           current_skills,
            'desired_skills':   desired_skills,
        }
