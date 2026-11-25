import pytest
from datetime import datetime
from unittest.mock import patch
from tasktracker.models import Task, db
from tasktracker.config import Config
import os


# 1. Use Fixture for authentication to adhere to DRY (Don't Repeat Yourself) principles
@pytest.fixture
def logged_in_client(client):
    """
    Setup process:
    Any test using this fixture will automatically be in a logged-in state.
    """
    client.post(
        "/login",
        json={"username": "admin", "password": "123"},
        follow_redirects=True,
    )
    yield client
    # Teardown logic can be added here (e.g., clearing sessions) if necessary


def test_index_page_content(client):
    """Test basic page accessibility (KISS principle)"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_add_task_behavior(logged_in_client):
    """
    Test task addition: Includes database state verification (Meaningful Assertions)
    """
    # Record the total count in the database before the operation
    initial_count = db.session.query(Task).count()

    task_data = {
        "name": "Learn TDD",
        "deadline": "2026-01-01 12:00:00",
        "description": "Keep testing!",
    }

    # Execute the addition via API
    response = logged_in_client.post("/api/tasks", json=task_data)
    assert response.status_code in [200, 201]  # Verify API return status

    # Verify that exactly one record was added to the database
    assert db.session.query(Task).count() == initial_count + 1

    # Verify the integrity of the latest data in the database (State-based Testing)
    new_task = db.session.query(Task).filter_by(name="Learn TDD").first()
    assert new_task is not None
    assert new_task.description == "Keep testing!"

    # Verify the task appears in the frontend API response
    get_response = logged_in_client.get("/api/tasks")
    assert b"Learn TDD" in get_response.data


def test_delete_task_behavior(logged_in_client):
    """Test task deletion: Verify data removal from both DB and API"""
    # Create a task first
    new_task = Task(
        name="Delete Me",
        deadline=datetime(2026, 1, 1, 12, 0, 0),  # Using datetime object
        description="This task will be deleted.",
    )
    db.session.add(new_task)
    db.session.commit()

    task_id = new_task.id

    # Simulate deletion operation
    delete_response = logged_in_client.delete(f"/api/tasks/{task_id}")
    assert delete_response.status_code == 200

    # Assert that the specific ID no longer exists in the database
    deleted_task = db.session.get(Task, task_id)
    assert deleted_task is None

    # Verify the API list no longer contains the deleted task
    get_response = logged_in_client.get("/api/tasks")
    assert b"Delete Me" not in get_response.data


def test_login_failed(client):
    """Test login failure path (Error Path)"""
    response = client.post(
        "/login", json={"username": "admin", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert b"Wrong username" in response.data


def test_add_task_form_missing_data(logged_in_client):
    """Test traditional HTML form submission with missing data"""
    # Send request without 'task_name'
    response = logged_in_client.post(
        "/add", data={"deadline": "2026-01-01T12:00"}, follow_redirects=True
    )
    assert b"Title and Deadline are required!" in response.data


def test_add_task_api_invalid_date(logged_in_client):
    """Test API task submission with an invalid date format"""
    response = logged_in_client.post(
        "/api/tasks",
        json={
            "name": "Invalid Date Task",
            "deadline": "not-a-date",
            "description": "test",
        },
    )
    assert response.status_code == 400
    assert b"Invalid date format" in response.data


def test_add_task_form_success(logged_in_client):
    """Coverage for Lines 96-143: Test successful traditional HTML form submission"""
    response = logged_in_client.post(
        "/add",
        data={
            "task_name": "Form Test Task",
            "description": "Testing the traditional form route",
            "deadline": "2026-12-31T23:59",  # Simulates 'T' format from HTML5 inputs
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Form Test Task" in response.data

    # Verify date normalization logic (replacing 'T' and padding seconds)

    task = Task.query.filter_by(name="Form Test Task").first()
    assert task.deadline.second == 0


def test_login_missing_data(client):
    """Coverage for Line 53: Test login API access with no data provided"""
    response = client.post("/login", json={})  # Sending empty JSON
    assert response.status_code == 400


def test_login_wrong_credentials(client):
    """Coverage for Lines 76-77: Test login with incorrect username or password"""
    response = client.post(
        "/login", json={"username": "admin", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert b"Wrong username or password" in response.data


def test_add_task_form_invalid_date_value(logged_in_client):
    """Coverage for ValueError block: Test submission of an unparsable date value"""
    response = logged_in_client.post(
        "/add",
        data={
            "task_name": "Bad Date Task",
            "deadline": "invalid-format-string",  # Triggers strptime error
        },
        follow_redirects=True,
    )
    # Verify flash message was triggered
    assert b"Invalid date format" in response.data
    # Verify no corrupted data was stored in the database
    from tasktracker.models import Task

    assert Task.query.filter_by(name="Bad Date Task").first() is None


def test_add_task_form_general_exception(logged_in_client):
    """Coverage for Exception block: Simulate unknown errors during DB commit"""
    # Simulate a RuntimeError occurring during db.session.commit
    with patch(
        "tasktracker.routes.page_routes.db.session.commit",
        side_effect=RuntimeError("DB Crash"),
    ):
        response = logged_in_client.post(
            "/add",
            data={"task_name": "Crash Task", "deadline": "2026-01-01T12:00"},
            follow_redirects=True,
        )
    # Verify general error message is displayed
    assert b"An unexpected error occurred" in response.data
    assert b"DB Crash" in response.data


def test_login_api_errors(client):
    """Specific coverage for error paths in the Login API"""
    # Fix for Line ~170: Send empty JSON {} instead of None
    # Ensures Content-Type is application/json but triggers 'if not data' logic
    res_no_data = client.post("/login", json={})
    assert res_no_data.status_code == 400

    # Coverage for Lines 76-77: Incorrect password via API
    res_wrong_pass = client.post(
        "/login", json={"username": "admin", "password": "wrong_password"}
    )
    assert res_wrong_pass.status_code == 401


def test_api_tasks_errors(logged_in_client):
    """Test error paths for task submission via API"""
    # Fix for Line ~180: Send empty JSON to trigger 'if not data'
    res_no_json = logged_in_client.post("/api/tasks", json={})
    assert res_no_json.status_code == 400

    # Coverage for Line 168: Missing required fields
    res_no_name = logged_in_client.post(
        "/api/tasks", json={"deadline": "2026-01-01 12:00:00"}
    )
    assert res_no_name.status_code == 400

    # Coverage for Lines 173, 175: Format errors
    res_bad_date = logged_in_client.post(
        "/api/tasks", json={"name": "test", "deadline": "bad-date"}
    )
    assert res_bad_date.status_code == 400


def test_api_tasks_general_exception(logged_in_client):
    """Coverage for Lines 192-194: Simulate DB crash during API submission"""
    # Simulate commit error during API save logic
    with patch(
        "tasktracker.routes.task_api_routes.db.session.commit",
        side_effect=Exception("API Database Error"),
    ):
        response = logged_in_client.post(
            "/api/tasks",
            json={"name": "API Crash Task", "deadline": "2026-01-01 12:00:00"},
        )

    # Verify that a 500 Internal Server Error is returned
    assert response.status_code == 500
    assert b"API Database Error" in response.data


def test_logout(logged_in_client):
    """Coverage for Lines 76-77: Test logout functionality"""
    response = logged_in_client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    # Verify session variables have been cleared
    with logged_in_client.session_transaction() as sess:
        assert "user_nickname" not in sess


def test_api_tasks_date_formatting(logged_in_client):
    """Coverage for Lines 173, 175: Test API handling of HTML5 datetime formats"""
    # Send "2026-01-01T12:00" (Length 16 and includes 'T')
    response = logged_in_client.post(
        "/api/tasks",
        json={
            "name": "Format Test",
            "deadline": "2026-01-01T12:00",
            "description": "test",
        },
    )
    assert response.status_code == 201
    # Verify the database correctly formatted the value
    from tasktracker.models import Task

    task = Task.query.filter_by(name="Format Test").first()
    assert task.deadline.second == 0  # Verify seconds were padded to :00


def test_config_ensure_instance_dir():
    """Coverage for config.py: Verify instance directory creation logic"""
    # Even if directory exists, calling this should cover the relevant lines
    Config.ensure_instance_dir()

    assert os.path.exists(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "instance")
    )


def test_config_logic():
    """Coverage for static methods in config.py"""
    from tasktracker.config import Config

    Config.ensure_instance_dir()
    # If this runs without error, lines in config.py are covered


def test_task_model_repr(client):  # Use client to trigger environment setup
    """Coverage for models.py: Test string representation of Task object"""

    # Create a task instance manually
    task = Task(name="Repr Test Task", deadline=datetime.now())

    # Triggering repr() covers the __repr__ method
    repr_string = repr(task)

    assert "Repr Test Task" in repr_string
    # Verify format matches <Task ...>
    assert repr_string.startswith("<Task")


def test_login_page_get(client):
    with client.session_transaction() as sess:
        sess["user_nickname"] = "testuser"

    response = client.get("/login", follow_redirects=True)
    assert response.status_code == 200
    assert b"TaskTracker" in response.data
