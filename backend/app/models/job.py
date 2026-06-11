from app import db
from datetime import datetime, timezone

class JobRaw(db.Model):
    __tablename__ = 'job_raw'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(30), nullable=False)
    source_id = db.Column(db.String(250), nullable=False)
    raw_payload = db.Column(db.JSON)
    is_processed = db.Column(db.Boolean, default=False)
    fetched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class JobListing(db.Model):
    __tablename__ = 'job_listings'

    id              = db.Column(db.Integer, primary_key=True)
    source          = db.Column(db.String(30), nullable=False)   # 'greenhouse', 'lever', 'ashby'
    source_id       = db.Column(db.String(250))                  # original ID from the ATS
    company         = db.Column(db.String(250))
    title           = db.Column(db.Text)
    department      = db.Column(db.Text)
    location        = db.Column(db.Text)
    
    # Updated: Replaced string sector with taxonomy links
    sector_id       = db.Column(db.Integer, db.ForeignKey('sector_taxonomy.id', ondelete='SET NULL'), nullable=True, index=True)
    role_id         = db.Column(db.Integer, db.ForeignKey('role_taxonomy.id', ondelete='SET NULL'), nullable=True, index=True)
    
    country         = db.Column(db.String(150), index=True)
    employment_type = db.Column(db.String(150))                   # Full-time, Part-time, Contract
    remote          = db.Column(db.Boolean, default=False, index=True)
    
    description     = db.Column(db.Text)
    url             = db.Column(db.Text)
    posted_at       = db.Column(db.DateTime)
    fetched_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Smart refresh fields:
    #   status = 'active'  → seen in the latest pipeline run
    #   status = 'expired' → NOT returned in the latest run (job filled/closed)
    #   status = 'unknown' → legacy rows before this feature was added
    status          = db.Column(db.String(20), default='active', index=True)
    last_seen_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_ai_enriched  = db.Column(db.Boolean, default=False)

    job_skills = db.relationship('JobSkill', backref='job', cascade='all, delete-orphan')
    sector = db.relationship('SectorTaxonomy', backref='job_listings')
    role = db.relationship('RoleTaxonomy', backref='job_listings')

    __table_args__ = (
        db.Index('idx_job_search', 'title', 'company', 'location'),
    )

    def to_dict(self):
        return {
            'id':              self.id,
            'source':          self.source,
            'company':         self.company,
            'title':           self.title,
            'department':      self.department,
            'location':        self.location,
            'sector':          self.sector.name if self.sector else None,
            'role':            self.role.title if self.role else None,
            'country':         self.country,
            'employment_type': self.employment_type,
            'remote':          self.remote,
            'status':          self.status,
            'skills':          [js.skill.canonical_name for js in self.job_skills if js.skill],
            'description':     self.description,
            'url':             self.url,
            'posted_at':       self.posted_at.isoformat() if self.posted_at else None,
            'last_seen_at':    self.last_seen_at.isoformat() if self.last_seen_at else None,
        }


class SkillTrend(db.Model):
    __tablename__ = 'skill_trends'

    id           = db.Column(db.Integer, primary_key=True)
    skill        = db.Column(db.String(100), nullable=False)
    count        = db.Column(db.Integer, default=0)     # number of jobs requiring this skill
    sector       = db.Column(db.String(100))            # e.g. 'Engineering', 'Data Science'
    period       = db.Column(db.String(20))             # e.g. '2025-Q1'
    computed_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'skill':       self.skill,
            'count':       self.count,
            'sector':      self.sector,
            'period':      self.period,
        }


class RoleTrend(db.Model):
    __tablename__ = 'role_trends'

    id          = db.Column(db.Integer, primary_key=True)
    role_title  = db.Column(db.String(200), nullable=False)
    sector      = db.Column(db.String(100))
    count       = db.Column(db.Integer, default=0)
    period      = db.Column(db.String(20))
    computed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'role':   self.role_title,
            'sector': self.sector,
            'count':  self.count,
            'period': self.period,
        }


class SectorTrend(db.Model):
    __tablename__ = 'sector_trends'

    id          = db.Column(db.Integer, primary_key=True)
    sector      = db.Column(db.String(100), nullable=False)
    total_jobs  = db.Column(db.Integer, default=0)
    growth_pct  = db.Column(db.Float, default=0.0)
    period      = db.Column(db.String(20))
    computed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'sector':     self.sector,
            'total_jobs': self.total_jobs,
            'growth_pct': self.growth_pct,
            'period':     self.period,
        }
