"""
Task API routing module.
Handles all task-related API endpoints for CRUD operations.
"""

from functools import wraps
from flask import request, jsonify, session
from tasktracker.routes import bp  # Import unified Blueprint instance
from tasktracker.models import Task, db
from tasktracker.routes.utils import parse_datetime_string


def get_authorized_tasks_query(current_user):
    """
    Return a query object based on user permissions.
    Admin users get all tasks, regular users get their own tasks.
    Returns None for unauthenticated users.
    """
    if current_user == "admin":
        return Task.query
    elif current_user:
        return Task.query.filter_by(author=current_user)
    return None


def apply_sorting(query, sort_order):
    """
    Apply sorting to a SQLAlchemy query.
    """
    if sort_order == "desc":
        return query.order_by(Task.deadline.desc())
    return query.order_by(Task.deadline.asc())


def validate_task_data(data):
    """
    Validate task creation/update data.
    Returns (is_valid, error_response) tuple.
    """
    task_name = data.get("name", "").strip()
    deadline_str = data.get("deadline", "").strip()
    description = data.get("description", "").strip()

    if not data:
        return False, (jsonify({"error": "No JSON data provided"}), 400)

    if not task_name or not deadline_str:
        return False, (jsonify({"error": "Task name and deadline are required"}), 400)

    return True, (task_name, deadline_str, description)


def handle_database_errors(func):
    """
    Database error handling decorator.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            # Specifically for date parsing errors from parse_datetime_string
            return jsonify({"error": "Invalid date format"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return wrapper


@bp.route("/api/tasks", methods=["GET"])
def get_tasks():
    """
    Handle fetching tasks (GET).
    Filter tasks based on user permissions (admin sees all, others see own).
    """
    # Get current user from session
    current_user = session.get("user_nickname")

    # Get sort order parameter, default to "asc" (ascending)
    sort_order = request.args.get("sort", "asc")

    # Get authorized query
    query = get_authorized_tasks_query(current_user)

    if query is None:
        # Unauthenticated users see no tasks
        return jsonify({"tasks": []})

    # Apply sorting and execute query
    query = apply_sorting(query, sort_order)
    tasks = query.all()

    return jsonify({"tasks": [task.to_dict() for task in tasks]})


@bp.route("/api/tasks", methods=["POST"])
@handle_database_errors
def create_task():
    """
    Create a new task (POST).
    """
    data = request.get_json()

    # Validate data using helper function
    is_valid, result = validate_task_data(data)
    if not is_valid:
        return result

    task_name, deadline_str, description = result
    author = session.get("user_nickname", "Unknown User")

    deadline = parse_datetime_string(deadline_str)

    new_task = Task(
        name=task_name,
        deadline=deadline,
        description=description,
        author=author,
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"success": True, "task": new_task.to_dict()}), 201


@bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@handle_database_errors
def delete_task_api(task_id):
    """
    Delete a specific task by ID.
    """
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"success": True}), 200


@bp.route("/api/tasks/<int:task_id>", methods=["PATCH"])
@handle_database_errors
def update_task_status(task_id):
    """
    Update task completion status.
    """
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json() or {}

    if "completed" in data:
        task.completed = data["completed"]

    db.session.commit()
    return jsonify({"success": True, "task": task.to_dict()}), 200


@bp.route("/api/tasks/<int:task_id>", methods=["PUT"])
@handle_database_errors
def update_task_api(task_id):
    """
    Update task details (name, deadline, description).
    """
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update fields if present
    if "name" in data:
        task.name = data["name"].strip()

    if "deadline" in data:
        deadline_str = data["deadline"].strip()
        task.deadline = parse_datetime_string(deadline_str)

    if "description" in data:
        task.description = data["description"].strip()

    db.session.commit()
    return jsonify({"success": True, "task": task.to_dict()}), 200


@bp.route("/api/tasks/bulk-delete", methods=["POST"])
@handle_database_errors
def bulk_delete_tasks():
    """
    Delete multiple tasks at once.
    """
    data = request.get_json() or {}
    task_ids = data.get("task_ids", [])

    if not task_ids:
        return jsonify({"error": "No task IDs provided"}), 400

    tasks = db.session.query(Task).filter(Task.id.in_(task_ids)).all()

    if not tasks:
        return jsonify({"error": "No valid tasks found"}), 404

    for task in tasks:
        db.session.delete(task)

    db.session.commit()
    return jsonify({"success": True, "deleted_ids": task_ids}), 200


@bp.route("/api/tasks/search", methods=["GET"])
def search_tasks():
    """
    Search tasks by name or description.
    """
    # Get current user from session
    current_user = session.get("user_nickname")

    # Get search term and sort order
    search_term = request.args.get("q", "").strip()
    sort_order = request.args.get("sort", "asc")

    # Get authorized query
    query = get_authorized_tasks_query(current_user)
    if query is None:
        # Unauthenticated users see no tasks
        return jsonify({"tasks": []})

    # Apply search filter if search term provided
    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Task.name.ilike(search_pattern), Task.description.ilike(search_pattern)
            )
        )

    # Apply sorting and execute query
    query = apply_sorting(query, sort_order)
    tasks = query.all()

    # Return results
    return jsonify({"tasks": [task.to_dict() for task in tasks]})
