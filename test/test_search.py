import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")

from tasktracker import create_app, db  # noqa: E402
from tasktracker.models import Task  # noqa: E402

# Create test app
app = create_app()
app.config.update(
    {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
    }
)


def test_search_functionality():
    with app.app_context():
        db.create_all()

        # Create test tasks
        tasks = [
            Task(
                name="Complete project report",
                description="Need to finish the final report",
                deadline=datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc),
                author="testuser",
            ),
            Task(
                name="Buy groceries",
                description="Milk, eggs, bread",
                deadline=datetime(2025, 1, 16, 10, 0, tzinfo=timezone.utc),
                author="testuser",
            ),
            Task(
                name="Meeting with team",
                description="Discuss project progress",
                deadline=datetime(2025, 1, 17, 9, 0, tzinfo=timezone.utc),
                author="testuser",
            ),
            Task(
                name="Gym workout",
                description="Cardio and weights",
                deadline=datetime(2025, 1, 18, 18, 0, tzinfo=timezone.utc),
                author="otheruser",
            ),
        ]

        for task in tasks:
            db.session.add(task)
        db.session.commit()

        # Create a test request context
        with app.test_request_context("/api/tasks/search?q=project"):
            # Mock session
            from flask import session

            session["user_nickname"] = "testuser"

            # Import and call the function
            import tasktracker.routes.task_api_routes as routes

            response = routes.search_tasks()

            print("Search results for 'project':")
            data = response.get_json()
            print(f"Number of tasks found: {len(data['tasks'])}")
            for task in data["tasks"]:
                print(f"  - {task['name']}: {task['description']}")

            # Should find 2 tasks (project report and meeting with project)
            assert len(data["tasks"]) == 2
            # Check that both tasks contain 'project' in name or description
            for task in data["tasks"]:
                assert (
                    "project" in task["name"].lower()
                    or "project" in (task["description"] or "").lower()
                )

        print("\n✅ Search test passed!")

        # Test search with empty term
        with app.test_request_context("/api/tasks/search?q="):
            session["user_nickname"] = "testuser"
            response = routes.search_tasks()
            data = response.get_json()
            msg = "\nEmpty search returns {} tasks (should be 3 for testuser)"
            print(msg.format(len(data["tasks"])))
            assert len(data["tasks"]) == 3  # testuser has 3 tasks

        print("✅ Empty search test passed!")

        # Test search with non-matching term
        with app.test_request_context("/api/tasks/search?q=nonexistent"):
            session["user_nickname"] = "testuser"
            response = routes.search_tasks()
            data = response.get_json()
            msg = "\nNon-matching search returns {} tasks (should be 0)"
            print(msg.format(len(data["tasks"])))
            assert len(data["tasks"]) == 0

        print("✅ Non-matching search test passed!")

        db.drop_all()


if __name__ == "__main__":
    try:
        test_search_functionality()
        print("\n🎉 All search tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
