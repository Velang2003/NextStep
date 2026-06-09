import redis
import json
import os
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Ping immediately to check health
            self.redis.ping()
            self.enabled = True
            logger.info(f"Connected to Redis cache successfully at {redis_url[:20]}...")
        except Exception as e:
            logger.warning(f"Redis cache is disabled. Failed to connect to Redis: {e}")
            self.enabled = False

    def get(self, key):
        if not self.enabled: return None
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except redis.exceptions.ConnectionError:
            self.enabled = False
            return None

    def set(self, key, value, timeout=3600):
        if not self.enabled: return
        try:
            self.redis.set(key, json.dumps(value), ex=timeout)
        except redis.exceptions.ConnectionError:
            self.enabled = False

    def delete(self, key):
        if not self.enabled: return
        try:
            self.redis.delete(key)
        except redis.exceptions.ConnectionError:
            self.enabled = False

    def clear_pattern(self, pattern):
        if not self.enabled: return
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except redis.exceptions.ConnectionError:
            self.enabled = False

cache_svc = CacheService()

def cached(key_prefix, timeout=3600):
    """Decorator to cache function results in Redis. Supports {g.user_id} in key_prefix."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import g
            # Resolve dynamic parts of the key_prefix
            resolved_prefix = key_prefix
            if "{g.user_id}" in resolved_prefix:
                uid = getattr(g, 'user_id', 'anon')
                resolved_prefix = resolved_prefix.replace("{g.user_id}", str(uid))
            
            # Create a unique key based on arguments
            arg_str = ":".join([str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()])
            cache_key = f"{resolved_prefix}:{arg_str}"
            
            result = cache_svc.get(cache_key)
            if result is not None:
                return result
            
            result = f(*args, **kwargs)
            # If the result is a Flask Response (e.g. from jsonify), we need to handle it
            # For simplicity, we'll assume these controllers return data that can be serialized
            # In Flask, a direct return from a route is often a Response object.
            # Let's check if it's a tuple (data, status) or a Response
            if hasattr(result, 'get_json'):
                cache_svc.set(cache_key, result.get_json(), timeout=timeout)
            elif isinstance(result, tuple) and hasattr(result[0], 'get_json'):
                # Handle (jsonify(data), 200)
                cache_svc.set(cache_key, result[0].get_json(), timeout=timeout)
            else:
                cache_svc.set(cache_key, result, timeout=timeout)
            return result
        return decorated_function
    return decorator
