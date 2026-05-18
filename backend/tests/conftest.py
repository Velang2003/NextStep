import pytest
from app import create_app, db as _db
from app.config import Config
from sqlalchemy import text

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    CELERY = {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,
    }

@pytest.fixture(scope='session')
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture(scope='session')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function', autouse=True)
def cleanup(app, db):
    """Automatically clear all tables after each test."""
    yield
    with app.app_context():
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

@pytest.fixture(scope='function')
def session(app, db):
    """Provide the database session to tests."""
    with app.app_context():
        yield db.session
