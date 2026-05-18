import pytest
from app.services.deduplicator import deduplicate_batch, _normalise_title, _normalise_company

def test_normalise_title():
    assert _normalise_title("Senior Software Engineer - Backend (Remote)") == "senior software engineer backend"
    assert _normalise_title("Junior Dev") == "junior dev"
    assert _normalise_title("Lead Designer [Hybrid]") == "lead designer"

def test_normalise_company():
    assert _normalise_company("Stripe, Inc.") == "stripe"
    assert _normalise_company("Google LLC") == "google"
    assert _normalise_company("Acme Corp.") == "acme"

def test_deduplicate_batch_exact():
    jobs = [
        {'source': 'greenhouse', 'source_id': '123', 'title': 'Job 1', 'company': 'Co 1'},
        {'source': 'greenhouse', 'source_id': '123', 'title': 'Job 1', 'company': 'Co 1'},
    ]
    unique, stats = deduplicate_batch(jobs)
    assert len(unique) == 1
    assert stats['by_source_id'] == 1

def test_deduplicate_batch_fingerprint():
    jobs = [
        {'source': 'greenhouse', 'source_id': '123', 'title': 'Software Engineer', 'company': 'Stripe'},
        {'source': 'lever',      'source_id': 'abc', 'title': 'Software Engineer', 'company': 'Stripe, Inc.'},
    ]
    unique, stats = deduplicate_batch(jobs)
    assert len(unique) == 1
    assert stats['by_fingerprint'] == 1

def test_deduplicate_batch_url():
    jobs = [
        {'source': 'greenhouse', 'source_id': '1', 'title': 'Eng 1', 'company': 'C1', 'url': 'https://jobs.com/1?ref=a'},
        {'source': 'lever',      'source_id': '2', 'title': 'Eng 2', 'company': 'C2', 'url': 'https://jobs.com/1?ref=b'},
    ]
    unique, stats = deduplicate_batch(jobs)
    assert len(unique) == 1
    assert stats['by_url'] == 1
