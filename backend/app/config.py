import os
from dotenv import load_dotenv
from datetime import timedelta
import warnings

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/nextstep_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
    }

    # Celery Configuration
    CELERY = {
        "broker_url": os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        "task_ignore_result": True,
    }

    SECRET_KEY     = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-prod')
    SENTRY_DSN     = os.getenv('SENTRY_DSN')
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

    # QuizAPI
    QUIZ_API_KEY = os.getenv('QUIZ_API_KEY', '')

    @classmethod
    def validate(cls):
        """Warn loudly in production if insecure defaults are in use."""
        if not os.getenv('FLASK_DEBUG') and 'dev-secret' in cls.SECRET_KEY:
            warnings.warn(
                "WARNING: Using default SECRET_KEY. Set SECRET_KEY env var in production!",
                RuntimeWarning, stacklevel=2
            )
