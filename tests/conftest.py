import sys
import os
import pytest
import fakeredis
from celery import current_app
from app.main import app as flask_app

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

@pytest.fixture(scope="session", autouse=True)
def celery_session_app(request):
    """Setup Celery for the test session."""
    celery_app = current_app
    celery_app.conf.update(task_always_eager=True)
    return celery_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_redis(monkeypatch):
    """Mocks the redis client for session management."""
    # The `decode_responses=True` is important to match the app's client behavior
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.new_session_manager.redis_client", fake_redis_client)
    yield fake_redis_client
    # Clean up the fake redis after the test
    fake_redis_client.flushall() 