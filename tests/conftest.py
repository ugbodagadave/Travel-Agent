import sys
import os
import pytest
from app.main import app
from app.database import init_db, SessionLocal, Base, engine

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def client():
    # Set up: configure app for testing
    app.config['TESTING'] = True
    
    # Use an in-memory SQLite database for tests
    test_db_url = 'sqlite:///:memory:'
    os.environ['DATABASE_URL'] = test_db_url
    
    # Re-initialize the database with the new test configuration
    init_db(db_url=test_db_url)

    with app.test_client() as client:
        with app.app_context():
            # Any setup that needs an app context can go here
            pass
        yield client

    # Teardown: Clean up resources
    # In-memory SQLite DB is automatically discarded, so no file cleanup needed.
    os.environ.pop('DATABASE_URL', None) 