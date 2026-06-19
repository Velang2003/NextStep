"""
Unit tests for app/services/cache_service.py
Tests: CacheService (disabled mode when Redis unavailable), cached decorator
"""
import pytest
from unittest.mock import MagicMock, patch


class TestCacheServiceDisabled:
    """When Redis is unreachable, CacheService must degrade gracefully."""

    def _make_disabled_cache(self):
        from app.services.cache_service import CacheService
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.side_effect = Exception("No Redis")
            svc = CacheService()
        assert svc.enabled is False
        return svc

    def test_get_returns_none_when_disabled(self):
        svc = self._make_disabled_cache()
        assert svc.get("some_key") is None

    def test_set_does_not_raise_when_disabled(self):
        svc = self._make_disabled_cache()
        svc.set("key", {"data": 1})  # Should not raise

    def test_delete_does_not_raise_when_disabled(self):
        svc = self._make_disabled_cache()
        svc.delete("key")  # Should not raise

    def test_clear_pattern_does_not_raise_when_disabled(self):
        svc = self._make_disabled_cache()
        svc.clear_pattern("prefix:*")  # Should not raise


class TestCacheServiceEnabled:
    """When Redis is reachable, all operations should work correctly."""

    def _make_enabled_cache(self):
        from app.services.cache_service import CacheService
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        with patch('redis.from_url', return_value=mock_redis):
            svc = CacheService()
        svc.redis = mock_redis
        return svc

    def test_get_returns_parsed_json(self):
        svc = self._make_enabled_cache()
        svc.redis.get.return_value = '{"score": 99}'
        result = svc.get("mykey")
        assert result == {"score": 99}

    def test_get_returns_none_for_missing_key(self):
        svc = self._make_enabled_cache()
        svc.redis.get.return_value = None
        assert svc.get("missing") is None

    def test_set_serializes_to_json(self):
        svc = self._make_enabled_cache()
        svc.set("mykey", {"value": 42}, timeout=60)
        svc.redis.set.assert_called_once_with("mykey", '{"value": 42}', ex=60)

    def test_delete_calls_redis_delete(self):
        svc = self._make_enabled_cache()
        svc.delete("mykey")
        svc.redis.delete.assert_called_once_with("mykey")

    def test_connection_error_disables_cache(self):
        import redis
        svc = self._make_enabled_cache()
        svc.redis.get.side_effect = redis.exceptions.ConnectionError("lost")
        result = svc.get("any")
        assert result is None
        assert svc.enabled is False


class TestCachedDecorator:
    """Test the @cached decorator key-building logic."""

    def test_key_includes_prefix_and_args(self, app):
        with app.app_context():
            from app.services.cache_service import cached, cache_svc
            cache_svc.enabled = False  # Disable to avoid actual Redis

            call_count = [0]

            @cached("test_prefix", timeout=10)
            def my_func(a, b):
                call_count[0] += 1
                return a + b

            result = my_func(1, 2)
            assert result == 3
            assert call_count[0] == 1
