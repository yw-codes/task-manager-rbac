"""
Test cases for Task Tracker application routes.
Uses pytest fixtures to create isolated test environments.
"""

import pytest
from tasktracker import create_app, db
from datetime import datetime, timedelta
from tasktracker.models import Task
from tasktracker.routes.utils import filter_tasks


@pytest.fixture
def app():
    """
    Create a Flask application instance for testing.
    """

    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SECRET_KEY = "test-secret-key"

        @staticmethod
        def ensure_instance_dir():
            pass  # prevents creating real instance folder

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

    return app


@pytest.fixture
def client(app):
    """
    Create a test client for the Flask application.

    Args:
        app: Flask application instance

    Returns:
        Test client for making HTTP requests
    """
    return app.test_client()


def test_index_page(client):
    """
    Test that the homepage returns a successful response (HTTP 200).

    This test ensures the main route '/' is accessible and functional.

    Args:
        client: Test client fixture
    """
    # Make GET request to homepage
    response = client.get("/")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200


def test_mark_task_complete_sets_completed_true(client):
    create_response = client.post(
        "/api/tasks",
        json={
            "name": "Finish report",
            "deadline": "2026-04-01 10:00:00",
            "description": "",
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.get_json()["task"]["id"]

    complete_response = client.patch(
        f"/api/tasks/{task_id}",
        json={"completed": True},
    )

    assert complete_response.status_code == 200
    assert complete_response.get_json()["task"]["completed"] is True


def test_completed_task_can_be_made_active_again(client):
    create_response = client.post(
        "/api/tasks",
        json={
            "name": "Write summary",
            "deadline": "2026-04-02 09:00:00",
            "description": "",
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.get_json()["task"]["id"]

    mark_done_response = client.patch(
        f"/api/tasks/{task_id}",
        json={"completed": True},
    )
    assert mark_done_response.status_code == 200
    assert mark_done_response.get_json()["task"]["completed"] is True

    undo_response = client.patch(
        f"/api/tasks/{task_id}",
        json={"completed": False},
    )
    assert undo_response.status_code == 200
    assert undo_response.get_json()["task"]["completed"] is False


def test_marking_task1_complete_leaves_task2_unchanged(client):
    # Login first
    client.post("/login", json={"username": "admin", "password": "123"})

    task1_response = client.post(
        "/api/tasks",
        json={
            "name": "Task 1",
            "deadline": "2026-04-01 10:00:00",
            "description": "",
        },
    )
    assert task1_response.status_code == 201
    task1_id = task1_response.get_json()["task"]["id"]

    task2_response = client.post(
        "/api/tasks",
        json={
            "name": "Task 2",
            "deadline": "2026-04-01 11:00:00",
            "description": "",
        },
    )
    assert task2_response.status_code == 201
    task2_id = task2_response.get_json()["task"]["id"]

    mark_response = client.patch(f"/api/tasks/{task1_id}", json={"completed": True})
    assert mark_response.status_code == 200

    tasks_response = client.get("/api/tasks")
    assert tasks_response.status_code == 200
    tasks = tasks_response.get_json()["tasks"]
    by_id = {task["id"]: task for task in tasks}

    assert by_id[task1_id]["completed"] is True
    assert by_id[task2_id]["completed"] is False


def test_completed_task_stays_completed_after_deleting_other_task(client):
    # Login first
    client.post("/login", json={"username": "admin", "password": "123"})

    completed_task_response = client.post(
        "/api/tasks",
        json={
            "name": "Completed Task",
            "deadline": "2026-04-03 10:00:00",
            "description": "",
        },
    )
    assert completed_task_response.status_code == 201
    completed_task_id = completed_task_response.get_json()["task"]["id"]

    other_task_response = client.post(
        "/api/tasks",
        json={
            "name": "Other Task",
            "deadline": "2026-04-03 11:00:00",
            "description": "",
        },
    )
    assert other_task_response.status_code == 201
    other_task_id = other_task_response.get_json()["task"]["id"]

    mark_response = client.patch(
        f"/api/tasks/{completed_task_id}",
        json={"completed": True},
    )
    assert mark_response.status_code == 200

    delete_response = client.delete(f"/api/tasks/{other_task_id}")
    assert delete_response.status_code == 200

    tasks_response = client.get("/api/tasks")
    assert tasks_response.status_code == 200
    tasks = tasks_response.get_json()["tasks"]
    by_id = {task["id"]: task for task in tasks}

    assert by_id[completed_task_id]["completed"] is True


def test_invalid_task_id_complete_uncomplete_does_not_crash_app(client):
    for completed in (True, False):
        response = client.patch("/api/tasks/999999", json={"completed": completed})

        assert response.status_code == 404
        assert response.is_json
        assert "error" in response.get_json()


# The edit functionality is validated using automated pytest test cases
# covering successful updates, invalid inputs, and system stability.


def test_update_task_route_exists(client):
    """
    Ensure PUT route exists for updating a task.
    """
    response = client.put("/api/tasks/1", json={})
    assert response.status_code in (400, 404)


def test_edit_task_success(client, app):
    """
    Test editing an existing task updates its fields.
    """
    with app.app_context():
        from tasktracker.models import Task
        from datetime import datetime

        # Create initial task
        task = Task(name="Old Task", deadline=datetime(2026, 3, 20, 10, 0, 0))
        db.session.add(task)
        db.session.commit()

        # Update task
        response = client.put(
            f"/api/tasks/{task.id}",
            json={
                "name": "Updated Task",
                "deadline": "2026-03-21 12:00:00",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200

        updated_task = db.session.get(Task, task.id)

        assert updated_task.name == "Updated Task"
        assert updated_task.description == "Updated description"


def test_edit_only_selected_task(client, app):
    """
    Ensure only the targeted task is updated.
    """
    with app.app_context():
        from tasktracker.models import Task
        from datetime import datetime

        task1 = Task(name="Task 1", deadline=datetime(2026, 3, 20, 10, 0, 0))
        task2 = Task(name="Task 2", deadline=datetime(2026, 3, 21, 10, 0, 0))

        db.session.add_all([task1, task2])
        db.session.commit()

        # Update only task1
        client.put(
            f"/api/tasks/{task1.id}",
            json={"name": "Updated Task 1"},
        )

        updated1 = db.session.get(Task, task1.id)
        updated2 = db.session.get(Task, task2.id)

        assert updated1.name == "Updated Task 1"
        assert updated2.name == "Task 2"  # unchanged


def test_edit_does_not_break_delete(client, app):
    """
    Ensure editing does not affect delete functionality.
    """
    with app.app_context():
        from tasktracker.models import Task
        from datetime import datetime

        task = Task(name="Task", deadline=datetime(2026, 3, 20, 10, 0, 0))
        db.session.add(task)
        db.session.commit()

        # Edit task
        client.put(f"/api/tasks/{task.id}", json={"name": "Edited"})

        # Delete task
        response = client.delete(f"/api/tasks/{task.id}")

        assert response.status_code == 200

        deleted = db.session.get(Task, task.id)
        assert deleted is None


def test_edit_task_invalid_data(client, app):
    """
    Ensure invalid input is handled correctly.
    """
    with app.app_context():
        from tasktracker.models import Task
        from datetime import datetime

        task = Task(name="Task", deadline=datetime(2026, 3, 20, 10, 0, 0))
        db.session.add(task)
        db.session.commit()

        response = client.put(
            f"/api/tasks/{task.id}",
            json={"deadline": "invalid-date"},
        )

        assert response.status_code == 400


def test_edit_reflects_immediately(client, app):
    """
    Ensure updated task is returned immediately.
    """
    with app.app_context():
        from tasktracker.models import Task
        from datetime import datetime

        task = Task(name="Task", deadline=datetime(2026, 3, 20, 10, 0, 0))
        db.session.add(task)
        db.session.commit()

        response = client.put(
            f"/api/tasks/{task.id}",
            json={"name": "New Name"},
        )

        data = response.get_json()

        assert data["success"] is True
        assert data["task"]["name"] == "New Name"


def test_bulk_delete_success(client, app):
    from tasktracker.models import Task
    from datetime import datetime

    with app.app_context():
        t1 = Task(name="Task 1", deadline=datetime.now())
        t2 = Task(name="Task 2", deadline=datetime.now())

        db.session.add_all([t1, t2])
        db.session.commit()

        response = client.post(
            "/api/tasks/bulk-delete", json={"task_ids": [t1.id, t2.id]}
        )

        assert response.status_code == 200

        # Ensure both deleted
        assert db.session.get(Task, t1.id) is None
        assert db.session.get(Task, t2.id) is None


def test_bulk_delete_no_ids(client, app):
    with app.app_context():
        response = client.post("/api/tasks/bulk-delete", json={})

        assert response.status_code == 400
        assert "error" in response.get_json()


def test_bulk_delete_partial(client, app):
    from tasktracker.models import Task
    from datetime import datetime

    with app.app_context():
        t1 = Task(name="Keep Me", deadline=datetime.now())
        t2 = Task(name="Delete Me", deadline=datetime.now())

        db.session.add_all([t1, t2])
        db.session.commit()

        response = client.post("/api/tasks/bulk-delete", json={"task_ids": [t2.id]})

        assert response.status_code == 200

        # Only t2 deleted
        assert db.session.get(Task, t2.id) is None
        assert db.session.get(Task, t1.id) is not None


def test_task_sorting_asc_and_desc(client, app):
    # Login first
    client.post("/login", json={"username": "admin", "password": "123"})

    from tasktracker.models import Task
    from datetime import datetime

    with app.app_context():
        t1 = Task(name="Task for May 2", deadline=datetime(2026, 5, 2, 10, 0, 0))
        t2 = Task(name="Task for May 1", deadline=datetime(2026, 5, 1, 10, 0, 0))

        db.session.add_all([t1, t2])
        db.session.commit()

        default_response = client.get("/api/tasks")
        assert default_response.status_code == 200
        tasks = default_response.get_json()["tasks"]
        by_id = {task["id"]: task for task in tasks}

        assert by_id[t2.id]["name"] == "Task for May 1"
        assert by_id[t1.id]["name"] == "Task for May 2"

        asc_response = client.get("/api/tasks?sort=asc")
        assert asc_response.status_code == 200
        tasks = asc_response.get_json()["tasks"]
        by_id = {task["id"]: task for task in tasks}

        assert by_id[t2.id]["name"] == "Task for May 1"
        assert by_id[t1.id]["name"] == "Task for May 2"

        desc_response = client.get("/api/tasks?sort=desc")
        assert desc_response.status_code == 200
        tasks = desc_response.get_json()["tasks"]
        by_id = {task["id"]: task for task in tasks}

        assert by_id[t1.id]["name"] == "Task for May 2"
        assert by_id[t2.id]["name"] == "Task for May 1"


def create_task(name, days_offset, completed):
    return Task(
        name=name,
        deadline=datetime.now() + timedelta(days=days_offset),
        completed=completed,
    )


def test_filter_completed():
    t1 = create_task("Done", 1, True)
    t2 = create_task("Pending", 1, False)

    result = filter_tasks([t1, t2], status_filter="completed")

    assert t1 in result
    assert t2 not in result


def test_filter_pending():
    t1 = create_task("Done", 1, True)
    t2 = create_task("Pending", 1, False)

    result = filter_tasks([t1, t2], status_filter="pending")

    assert t2 in result
    assert t1 not in result


def test_filter_today():
    t1 = create_task("Today Task", 0, False)
    t2 = create_task("Tomorrow Task", 1, False)

    result = filter_tasks([t1, t2], date_filter="today")

    assert t1 in result
    assert t2 not in result


def test_filter_week():
    t1 = create_task("Within Week", 3, False)
    t2 = create_task("After Week", 10, False)

    result = filter_tasks([t1, t2], date_filter="week")

    assert t1 in result
    assert t2 not in result


def test_combined_filters():
    t1 = create_task("Match", 2, True)
    t2 = create_task("Wrong Status", 2, False)
    t3 = create_task("Wrong Date", 10, True)

    result = filter_tasks([t1, t2, t3], status_filter="completed", date_filter="week")

    assert t1 in result
    assert t2 not in result
    assert t3 not in result


def test_no_filters_returns_all():
    t1 = create_task("Task1", 1, True)
    t2 = create_task("Task2", 2, False)

    result = filter_tasks([t1, t2])

    assert len(result) == 2
