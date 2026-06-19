"""
Unit tests for app/services/gap_analysis_service.py
Tests: calculate_skill_gap (cosine similarity logic, edge cases)
"""
import math
import pytest


# ──────────────────────────────────────────────
# Isolated unit tests — pure logic, no DB needed
# ──────────────────────────────────────────────

class TestCosineLogic:
    """
    Test the cosine similarity math used in calculate_skill_gap directly.

    Service logic (from gap_analysis_service.py):
      vocab = list(known_skills | required_skills)
      if not vocab:
          match_percentage = 100.0 if not required_skills else 0.0
      else:
          # ... cosine calculation
          if mag_profile == 0 or mag_job == 0:
              similarity = 0.0
    """

    def _cosine(self, known: set, required: set) -> float:
        """Exact replica of gap_analysis_service calculation."""
        vocab = list(known | required)
        if not vocab:
            return 100.0 if not required else 0.0
        pv = [1 if s in known else 0 for s in vocab]
        jv = [1 if s in required else 0 for s in vocab]
        dot = sum(p * j for p, j in zip(pv, jv))
        mp = math.sqrt(sum(p * p for p in pv))
        mj = math.sqrt(sum(j * j for j in jv))
        if mp == 0 or mj == 0:
            return 0.0
        return round((dot / (mp * mj)) * 100, 1)

    def test_perfect_match(self):
        skills = {"Python", "React", "SQL"}
        assert self._cosine(skills, skills) == 100.0

    def test_zero_overlap(self):
        known = {"Python", "Django"}
        required = {"Java", "Spring"}
        assert self._cosine(known, required) == 0.0

    def test_partial_match(self):
        known = {"Python", "SQL"}
        required = {"Python", "SQL", "React"}
        score = self._cosine(known, required)
        assert 0 < score < 100

    def test_both_empty_returns_100(self):
        """When neither profile nor job has skills, result is 100%."""
        assert self._cosine(set(), set()) == 100.0

    def test_known_only_no_required_returns_0(self):
        """Known skills but no required → mj=0 → similarity=0 (no job vector)."""
        assert self._cosine({"Python"}, set()) == 0.0

    def test_empty_known(self):
        assert self._cosine(set(), {"Python", "React"}) == 0.0

    def test_score_increases_with_more_matches(self):
        required = {"A", "B", "C", "D"}
        s1 = self._cosine({"A"}, required)
        s2 = self._cosine({"A", "B"}, required)
        s3 = self._cosine({"A", "B", "C"}, required)
        assert s1 < s2 < s3

    def test_score_is_bounded_0_to_100(self):
        for known_count in range(0, 5):
            known = set(list("ABCDE")[:known_count])
            required = {"A", "B", "C"}
            score = self._cosine(known, required)
            assert 0.0 <= score <= 100.0


# ──────────────────────────────────────────────
# Integration tests — use in-memory DB
# ──────────────────────────────────────────────

class TestCalculateSkillGap:
    """Integration tests against SQLite in-memory DB."""

    def test_missing_profile_returns_error(self, session, app):
        with app.app_context():
            from app.services.gap_analysis_service import calculate_skill_gap
            result = calculate_skill_gap(99999, 99999)
            assert 'error' in result

    def test_missing_job_returns_error(self, session, app):
        from app.models.user import User, Profile
        with app.app_context():
            u = User(email="test_gap@ex.com", password_hash="x")
            session.add(u)
            session.flush()
            p = Profile(user_id=u.id)
            session.add(p)
            session.commit()

            from app.services.gap_analysis_service import calculate_skill_gap
            result = calculate_skill_gap(p.id, 99999)
            assert 'error' in result

    def test_gap_analysis_no_skills(self, session, app):
        from app.models.user import User, Profile
        from app.models.job import JobListing
        with app.app_context():
            u = User(email="nogap@ex.com", password_hash="x")
            session.add(u)
            session.flush()
            p = Profile(user_id=u.id)
            session.add(p)
            j = JobListing(
                title="Dev", company="Co", source="test",
                source_id="jgap1", location="Remote"
            )
            session.add(j)
            session.commit()

            from app.services.gap_analysis_service import calculate_skill_gap
            result = calculate_skill_gap(p.id, j.id)
            assert 'error' not in result
            assert result['match_percentage'] == 100.0  # no required skills → full match
            assert result['gap'] == []
