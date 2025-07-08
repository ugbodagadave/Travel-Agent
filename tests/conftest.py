import sys
import os
import pytest
import fakeredis
from app.main import app as flask_app

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

@pytest.fixture(scope="function")
def client():
    # Set up: configure app for testing
    flask_app.config['TESTING'] = True
    
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

@pytest.fixture
def mock_redis(monkeypatch):
    """Mocks the redis client for session management."""
    # The `decode_responses=True` is important to match the app's client behavior
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.new_session_manager.redis_client", fake_redis_client)
    yield fake_redis_client
    # Clean up the fake redis after the test
    fake_redis_client.flushall() 