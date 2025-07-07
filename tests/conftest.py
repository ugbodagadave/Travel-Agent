import sys
import os
import pytest
import fakeredis
from app.main import app
from app.database import init_db, SessionLocal, Base, engine
 
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

@pytest.fixture(scope="function")
def client():
    # Set up: configure app for testing
    app.config['TESTING'] = True
    
    # Use an in-memory SQLite database for tests
    test_db_url = 'sqlite:///:memory:'
    
    # Re-initialize the database with the new test configuration
    init_db(db_url=test_db_url)

    # Create tables before each test
    Base.metadata.create_all(bind=engine)

    with app.test_client() as client:
        with app.app_context():
            yield client

    # Teardown: Clean up the database after each test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(client, monkeypatch):
    """
    Provides a transactional database session for a test.
    It also patches SessionLocal to return this same session,
    ensuring the app code and test code use the same transaction.
    """
    session = SessionLocal()
    monkeypatch.setattr("app.database.SessionLocal", lambda: session)
    
    try:
        yield session
    finally:
        session.rollback() # Rollback to not affect other tests
        session.close()

@pytest.fixture
def mock_redis(monkeypatch):
    """Mocks the redis client for session management."""
    # The `decode_responses=True` is important to match the app's client behavior
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.new_session_manager.redis_client", fake_redis_client)
    yield fake_redis_client
    # Clean up the fake redis after the test
    fake_redis_client.flushall() 