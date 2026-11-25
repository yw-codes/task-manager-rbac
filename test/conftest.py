import pytest
import sys
import os
from tasktracker import db
from tasktracker import app as flask_app

# Ensure the project root is in the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session")
def app():
    """
    Session-wide test application setup.
    Uses an In-Memory SQLite database to ensure tests are fast and isolated.
    """
    params = {
        "TESTING": True,
        # Use in-memory database to avoid touching the actual 'instance/app.db'
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for easier API testing
    }

    # Assuming you have a factory pattern or a way to update config

    flask_app.config.update(params)

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    """
    A Flask test client for the duration of a single test.
    """
    return app.test_client()


@pytest.fixture(autouse=True)
def setup_test_database(app):
    """
    Ensures a clean database state for every single test case.
    Rolls back any changes made during a test to maintain atomicity.
    """
    with app.app_context():
        # Clear data before each test if not using a fresh in-memory DB per test
        # For SQLite in-memory, db.create_all() in 'app' fixture is often enough
        yield
        db.session.rollback()  # Crucial: prevents cross-test data pollution
        db.session.remove()
