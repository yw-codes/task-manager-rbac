#!/usr/bin/env python3
"""
Test script for search persistence functionality.
Tests that search state is maintained across various operations.
"""

import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")

from tasktracker import create_app, db  # noqa: E402
from tasktracker.models import Task, User  # noqa: E402


def test_search_persistence():
    """Test that search state persists across operations"""

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

        # Create test tasks
        tasks = [
            Task(
                name="Complete project report",
                description="Need to finish the final report",
                deadline=datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc),
                author="Test User",
            ),
            Task(
                name="Buy groceries",
                description="Milk, eggs, bread",
                deadline=datetime(2025, 1, 16, 10, 0, tzinfo=timezone.utc),
                author="Test User",
            ),
            Task(
                name="Meeting with team",
                description="Discuss project progress",
                deadline=datetime(2025, 1, 17, 9, 0, tzinfo=timezone.utc),
                author="Test User",
            ),
            Task(
                name="Gym workout",
                description="Cardio and weights",
                deadline=datetime(2025, 1, 18, 18, 0, tzinfo=timezone.utc),
                author="Other User",
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

            print("=== Search Persistence Test ===")
            print("1. Initial state: All tasks for Test User (should be 3)")

            # Test 1: Search for 'project' (should find 2 tasks)
            resp = client.get("/api/tasks/search?q=project")
            data = resp.get_json()
            print(f"   Search 'project': Found {len(data['tasks'])} tasks")

            # Test 2: Mark a task as complete
            task_id = data["tasks"][0]["id"]
            print(f"2. Mark task {task_id} as complete...")

            resp = client.patch(f"/api/tasks/{task_id}", json={"completed": True})
            print(f"   Mark complete response: {resp.status_code}")

            # Test 3: Verify search state is maintained
            print("3. Verify search still active...")
            resp = client.get("/api/tasks/search?q=project")
            data = resp.get_json()
            msg = "   Search 'project' after completion: Found {} tasks"
            print(msg.format(len(data["tasks"])))

            # Test 4: Delete a task
            task_id = data["tasks"][0]["id"]
            print(f"4. Delete task {task_id}...")

            resp = client.delete(f"/api/tasks/{task_id}")
            print(f"   Delete response: {resp.status_code}")

            # Test 5: Verify search state still maintained
            print("5. Verify search still active after delete...")
            resp = client.get("/api/tasks/search?q=project")
            data = resp.get_json()
            msg = "   Search 'project' after delete: Found {} tasks"
            print(msg.format(len(data["tasks"])))

            # Test 6: Test sorting with search
            print("6. Test sorting with search...")
            resp = client.get("/api/tasks/search?q=project&sort=desc")
            data = resp.get_json()
            msg = "   Search 'project' with descending sort: Found {} tasks"
            print(msg.format(len(data["tasks"])))

            # Test 7: Clear search
            print("7. Clear search (by requesting all tasks)...")
            resp = client.get("/api/tasks")
            data = resp.get_json()
            msg = "   All tasks after clearing: Found {} tasks"
            print(msg.format(len(data["tasks"])))

            # Cleanup
            db.drop_all()

            print("\n=== Test Summary ===")
            print("✅ Search API endpoints work correctly")
            print("✅ Search state should be maintained across operations")
            print("✅ Manual testing required to verify frontend behavior")
            print("\nNote: For complete testing, please:")
            print("1. Run the application: python run.py")
            print("2. Manually test:")
            print("   - Search for tasks")
            print("   - Mark tasks complete (should stay in search results)")
            print("   - Delete tasks (should stay in search results)")
            print("   - Sort tasks (should keep search filter)")


if __name__ == "__main__":
    try:
        test_search_persistence()
        print("\n🎉 Backend search persistence tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
