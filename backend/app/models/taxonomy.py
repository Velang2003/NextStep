"""
Database-driven taxonomy models for skills, sectors, and roles.
All classification data lives in the DB — nothing hardcoded in source.
"""
from app import db
from datetime import datetime, timezone


class SkillTaxonomy(db.Model):
    __tablename__ = 'skill_taxonomy'

    id = db.Column(db.Integer, primary_key=True)
    canonical_name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(60), nullable=False)  # Language, Framework, Cloud, Tool, etc.
    sector_id = db.Column(db.Integer, db.ForeignKey('sector_taxonomy.id'), nullable=True)  # NULL = cross-sector
    description = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sector = db.relationship('SectorTaxonomy', backref='skills')
    aliases = db.relationship('SkillAlias', backref='skill', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.canonical_name,
            'category': self.category,
            'sector': self.sector.name if self.sector else None,
            'sector_id': self.sector_id,
            'aliases': [a.name for a in self.aliases],
        }


class SkillAlias(db.Model):
    __tablename__ = 'skill_alias'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_taxonomy.id'), nullable=False)


class SectorTaxonomy(db.Model):
    __tablename__ = 'sector_taxonomy'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    aliases = db.relationship('SectorAlias', backref='sector', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'aliases': [a.name for a in self.aliases],
        }


class SectorAlias(db.Model):
    __tablename__ = 'sector_alias'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector_taxonomy.id'), nullable=False)


class RoleTaxonomy(db.Model):
    __tablename__ = 'role_taxonomy'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector_taxonomy.id'), nullable=True)
    seniority = db.Column(db.String(30))  # Junior, Mid, Senior, Lead, Principal
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sector = db.relationship('SectorTaxonomy', backref='roles')
    aliases = db.relationship('RoleAlias', backref='role', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'sector': self.sector.name if self.sector else None,
            'seniority': self.seniority,
            'aliases': [a.name for a in self.aliases],
        }


class RoleAlias(db.Model):
    __tablename__ = 'role_alias'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role_taxonomy.id'), nullable=False)


class RoleSkill(db.Model):
    """Many-to-many association: which skills are required for which role."""
    __tablename__ = 'role_skill'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role_taxonomy.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_taxonomy.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('role_id', 'skill_id', name='uq_role_skill'),)

    role = db.relationship('RoleTaxonomy', backref=db.backref('role_skills', cascade='all, delete-orphan'))
    skill = db.relationship('SkillTaxonomy', backref=db.backref('role_skills', cascade='all, delete-orphan'))


class CountryMapping(db.Model):
    """Maps city/region names and aliases to ISO-3166 country codes."""
    __tablename__ = 'country_mapping'

    id = db.Column(db.Integer, primary_key=True)
    country_name = db.Column(db.String(100), nullable=False)
    iso3 = db.Column(db.String(3), nullable=False)
    iso2 = db.Column(db.String(2), nullable=False)
    aliases = db.Column(db.JSON, default=list)  # city names, abbreviations, etc.
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    def to_dict(self):
        return {
            'country': self.country_name,
            'iso3': self.iso3,
            'iso2': self.iso2,
            'lat': self.lat,
            'lng': self.lng,
        }


class PendingSkill(db.Model):
    """
    Admin review queue for newly discovered / user-suggested skills.
    Skills stay here until an admin approves (→ SkillTaxonomy) or rejects them.
    """
    __tablename__ = 'pending_skills'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(150), nullable=False)
    suggested_category = db.Column(db.String(60))          # Language, Framework, Tool, etc.
    suggested_role_id  = db.Column(db.Integer, db.ForeignKey('role_taxonomy.id'), nullable=True)
    source         = db.Column(db.String(60))              # 'pipeline', 'user', 'gemini'
    source_detail  = db.Column(db.String(250))             # e.g. job URL or user email
    status         = db.Column(db.String(20), default='pending')  # pending | approved | rejected
    admin_note     = db.Column(db.Text)
    submitted_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at    = db.Column(db.DateTime)
    reviewed_by    = db.Column(db.String(120))             # admin email

    suggested_role = db.relationship('RoleTaxonomy', foreign_keys=[suggested_role_id])

    def to_dict(self):
        return {
            'id':                 self.id,
            'name':               self.name,
            'suggested_category': self.suggested_category,
            'suggested_role':     self.suggested_role.title if self.suggested_role else None,
            'suggested_role_id':  self.suggested_role_id,
            'source':             self.source,
            'source_detail':      self.source_detail,
            'status':             self.status,
            'admin_note':         self.admin_note,
            'submitted_at':       self.submitted_at.isoformat() if self.submitted_at else None,
            'reviewed_at':        self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by':        self.reviewed_by,
        }


class PendingRole(db.Model):
    """
    Queue for newly discovered roles that don't match the current taxonomy.
    Allows expanding beyond IT by letting AI suggest new sectors/roles for admin review.
    """
    __tablename__ = 'pending_roles'

    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(150), nullable=False)
    suggested_sector = db.Column(db.String(100))
    source           = db.Column(db.String(60))              # 'gemini', 'seed_script'
    source_detail    = db.Column(db.String(250))             # Job title @ Company
    status           = db.Column(db.String(20), default='pending')
    admin_note       = db.Column(db.Text)
    submitted_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at      = db.Column(db.DateTime)
    reviewed_by      = db.Column(db.String(120))

    def to_dict(self):
        return {
            'id':               self.id,
            'title':            self.title,
            'suggested_sector': self.suggested_sector,
            'source':           self.source,
            'source_detail':    self.source_detail,
            'status':           self.status,
            'submitted_at':     self.submitted_at.isoformat() if self.submitted_at else None,
        }


class KeywordDiscovery(db.Model):
    __tablename__ = 'keyword_discovery'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), default='skill') # 'skill' or 'role'
    frequency = db.Column(db.Integer, default=1)
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    suggested_sector = db.Column(db.String(100))
    source_detail = db.Column(db.Text)

    __table_args__ = (db.UniqueConstraint('name', 'type', name='_name_type_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'frequency': self.frequency,
            'last_seen': self.last_seen.isoformat(),
        }

