"""
Unit tests for app/services/data_normalizer.py — location normalizer
Tests: normalize_location (no DB needed for URL/remote detection)
"""
import pytest
from app.services.data_normalizer import normalize_location, invalidate_cache


class TestNormalizeLocation:
    """Test normalize_location's remote-detection and empty-string handling."""

    def test_empty_string(self):
        result = normalize_location('')
        assert result == {'location': '', 'country': '', 'country_iso3': '', 'remote': False}

    def test_none_input(self):
        result = normalize_location(None)
        assert result == {'location': '', 'country': '', 'country_iso3': '', 'remote': False}

    def test_remote_keyword_detected(self):
        result = normalize_location('Remote')
        assert result['remote'] is True

    def test_anywhere_keyword_detected(self):
        result = normalize_location('Work from anywhere')
        assert result['remote'] is True

    def test_distributed_keyword_detected(self):
        result = normalize_location('Fully distributed team')
        assert result['remote'] is True

    def test_work_from_home_detected(self):
        result = normalize_location('Work from home')
        assert result['remote'] is True

    def test_non_remote_office(self):
        result = normalize_location('New York, NY')
        assert result['remote'] is False

    def test_location_preserved(self):
        loc_str = 'San Francisco, CA'
        result = normalize_location(loc_str)
        assert result['location'] == loc_str

    def test_result_has_all_keys(self):
        result = normalize_location('London')
        for key in ('location', 'country', 'country_iso3', 'remote'):
            assert key in result


class TestNormalizeLocationWithDB:
    """DB-seeded tests for country detection."""

    def test_country_detection_by_alias(self, session, app):
        from app.models.taxonomy import CountryMapping
        with app.app_context():
            c = CountryMapping(
                country_name='India',
                iso2='IN',
                iso3='IND',
                aliases=['india', 'ind'],
                lat=20.0, lng=77.0
            )
            session.add(c)
            session.commit()
            invalidate_cache()

            result = normalize_location('Bangalore, India')
            assert result['country'] == 'India'
            assert result['country_iso3'] == 'IND'

    def test_unknown_country_returns_empty(self, session, app):
        with app.app_context():
            invalidate_cache()
            result = normalize_location('Narnia')
            assert result['country'] == ''
            assert result['country_iso3'] == ''
