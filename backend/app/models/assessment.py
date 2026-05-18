"""
Skill assessment models — tracks MCQ quiz attempts and per-question results.
"""
from app import db
from datetime import datetime, timezone


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_taxonomy.id', ondelete='CASCADE'), nullable=False)
    difficulty = db.Column(db.String(20), default='medium')
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
    passed = db.Column(db.Boolean, default=False)
    learning_path_recommended = db.Column(db.JSON)
    taken_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='assessments')
    skill = db.relationship('SkillTaxonomy')
    questions = db.relationship('AssessmentQuestion', backref='assessment',
                                cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'skill_name': self.skill.canonical_name if self.skill else None,
            'difficulty': self.difficulty,
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': self.percentage,
            'passed': self.passed,
            'learning_path_recommended': self.learning_path_recommended,
            'taken_at': self.taken_at.isoformat() if self.taken_at else None,
        }


class AssessmentQuestion(db.Model):
    __tablename__ = 'assessment_questions'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text, nullable=True)       # code block shown above options
    options = db.Column(db.JSON)  # {"a": "...", "b": "...", "c": "...", "d": "..."}
    correct_answer = db.Column(db.String(10))
    explanation = db.Column(db.Text, nullable=True)        # shown in results review
    user_answer = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean)

    def to_dict(self, include_answer=False):
        d = {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'question': self.question_text,
            'code_snippet': self.code_snippet or '',
            'options': self.options,
        }
        if include_answer:
            d['correct_answer'] = self.correct_answer
            d['user_answer'] = self.user_answer
            d['is_correct'] = self.is_correct
            d['explanation'] = self.explanation or ''
        return d


class QuestionBank(db.Model):
    __tablename__ = 'question_bank'

    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_taxonomy.id', ondelete='CASCADE'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text, nullable=True)
    options = db.Column(db.JSON)  # {"a": "...", "b": "...", "c": "...", "d": "..."}
    correct_answer = db.Column(db.String(10))
    explanation = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    skill = db.relationship('SkillTaxonomy')

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question_text,
            'code_snippet': self.code_snippet or '',
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation or '',
        }
