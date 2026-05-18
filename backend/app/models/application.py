"""
Job application tracking models — save/bookmark jobs and track application status.
"""
from app import db
from datetime import datetime, timezone


class JobApplication(db.Model):
    __tablename__ = 'job_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_listings.id'), nullable=False)
    status = db.Column(db.String(30), default='saved')  # saved, applied, interviewing, offered, rejected
    notes = db.Column(db.Text)
    applied_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='applications')
    job = db.relationship('JobListing', backref='applications')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='uq_user_job'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'status': self.status,
            'notes': self.notes,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'job': self.job.to_dict() if self.job else None,
        }
