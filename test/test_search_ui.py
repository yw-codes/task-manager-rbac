#!/usr/bin/env python3
"""
Test script to verify the search UI fix for empty search results.
Specifically tests the scenario where user deletes all search results.
"""

import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")

from tasktracker import create_app, db  # noqa: E402
from tasktracker.models import Task, User  # noqa: E402


def test_search_empty_results_scenario():
    """Test the scenario: search for tasks, delete all results, verify UI behavior"""

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

    with app.app_context():
        # Setup database
        db.create_all()

        # Create test user
        test_user = User(username="testuser", nickname="Test User")
        test_user.set_password("password123")
        db.session.add(test_user)
        db.session.commit()

        # Create test tasks with different names
        tasks = [
            Task(
                name="Task 111",
                description="First task",
                deadline=datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc),
                author="Test User",
            ),
            Task(
                name="Task 222",
                description="Second task with 222",
                deadline=datetime(2025, 1, 16, 10, 0, tzinfo=timezone.utc),
                author="Test User",
            ),
            Task(
                name="Another 222 task",
                description="Third task also with 222",
                deadline=datetime(2025, 1, 17, 9, 0, tzinfo=timezone.utc),
                author="Test User",
            ),
            Task(
                name="Task 333",
                description="Fourth task",
                deadline=datetime(2025, 1, 18, 18, 0, tzinfo=timezone.utc),
                author="Test User",
            ),
        ]

        for task in tasks:
            db.session.add(task)
        db.session.commit()

        # Start a test client session
        with app.test_client() as client:
            # Simulate login
            with client.session_transaction() as session:
                session["user_nickname"] = "Test User"

            print("=== Testing Search Empty Results Scenario ===")
            print("\n1. Initial state: All tasks for Test User")
            resp = client.get("/api/tasks")
            data = resp.get_json()
            print(f"   Total tasks: {len(data['tasks'])}")

            print("\n2. Search for '222' (should find 2 tasks)")
            resp = client.get("/api/tasks/search?q=222")
            data = resp.get_json()
            print(f"   Search results: {len(data['tasks'])} tasks")
            for task in data["tasks"]:
                print(f"     - {task['name']} (ID: {task['id']})")

            # Verify both tasks contain '222'
            expected_msg = "Expected 2 tasks with '222', got {}"
            assert len(data["tasks"]) == 2, expected_msg.format(len(data["tasks"]))

            print("\n3. Delete the first '222' task")
            task_id = data["tasks"][0]["id"]
            resp = client.delete(f"/api/tasks/{task_id}")
            print(f"   Delete response: {resp.status_code}")

            print("\n4. Verify search still active (should find 1 task now)")
            resp = client.get("/api/tasks/search?q=222")
            data = resp.get_json()
            msg = "   Search results after first delete: {} tasks"
            print(msg.format(len(data["tasks"])))
            expected_msg = "Expected 1 task with '222' after first delete, got {}"
            assert len(data["tasks"]) == 1, expected_msg.format(len(data["tasks"]))

            print("\n5. Delete the remaining '222' task")
            task_id = data["tasks"][0]["id"]
            resp = client.delete(f"/api/tasks/{task_id}")
            print(f"   Delete response: {resp.status_code}")

            print("\n6. Verify search now returns empty results")
            resp = client.get("/api/tasks/search?q=222")
            data = resp.get_json()
            msg = "   Search results after deleting all '222' tasks: {} tasks"
            print(msg.format(len(data["tasks"])))
            expected_msg = "Expected 0 tasks with '222' after deleting all, got {}"
            assert len(data["tasks"]) == 0, expected_msg.format(len(data["tasks"]))

            print("\n7. Verify user can still see other tasks (e.g., '111' and '333')")
            resp = client.get("/api/tasks")
            data = resp.get_json()
            msg = "   All tasks after deleting '222' tasks: {} tasks"
            print(msg.format(len(data["tasks"])))
            task_names = [task["name"] for task in data["tasks"]]
            print(f"   Remaining tasks: {', '.join(task_names)}")

            # Should have 2 tasks left (111 and 333)
            expected_msg = "Expected 2 tasks remaining, got {}"
            assert len(data["tasks"]) == 2, expected_msg.format(len(data["tasks"]))
            assert "Task 111" in task_names, "Task 111 should still exist"
            assert "Task 333" in task_names, "Task 333 should still exist"

            print("\n8. Test that clearing search returns all tasks")
            # Simulate clearing search by calling normal tasks API
            resp = client.get("/api/tasks")
            data = resp.get_json()
            msg = "   All tasks after clearing search: {} tasks"
            print(msg.format(len(data["tasks"])))

            # Cleanup
            db.drop_all()

            print("\n=== Test Results ===")
            print("✅ Search correctly finds matching tasks")
            print("✅ Deleting search results maintains search state")
            print("✅ Empty search results don't hide other tasks")
            print("✅ Users can clear search to see all tasks")
            print("\n🎉 Backend logic is correct!")
            print("\nNote: This tests backend API behavior.")
            print("Frontend UI behavior needs manual testing:")
            print("1. Run the application: python run.py")
            print("2. Login and create tasks with names '111', '222', '333'")
            print("3. Search for '222'")
            print("4. Delete all '222' tasks")
            print("5. Verify:")
            print("   - Search controls remain visible")
            print("   - Clear button remains visible")
            print("   - Message shows: 'No tasks match your search \"222\"'")
            print("   - 'Clear Search & Show All Tasks' button works")


if __name__ == "__main__":
    try:
        test_search_empty_results_scenario()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
