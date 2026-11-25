"""
Page rendering routing module.
Handles HTML page rendering and form submissions.
"""

from flask import render_template, request, redirect, url_for, flash, session
from tasktracker.routes import bp  # Import unified Blueprint instance
from tasktracker.models import Task, db
from tasktracker.routes.utils import parse_datetime_string


@bp.route("/")
def index():
    """
    Render main page with tasks from database filtered by current user.
    Admin sees all tasks, other users see only their own tasks.
    """
    # Get current user nickname from session
    current_user = session.get("user_nickname")

    # Filter tasks based on user permissions
    if current_user == "admin":
        # Admin sees all tasks
        tasks = Task.query.order_by(Task.deadline.asc()).all()
    elif current_user:
        # Logged-in users see only their own tasks
        tasks = (
            Task.query.filter_by(author=current_user)
            .order_by(Task.deadline.asc())
            .all()
        )
    else:
        # Unauthenticated users see no tasks
        tasks = []

    return render_template(
        "index.html",
        tasks=[task.to_dict() for task in tasks],
        current_user=current_user,
    )


@bp.route("/add", methods=["POST"])
def add_task():
    """
    Handle traditional form submission for adding a task.
    """
    # 1. request.form.get() retrieves form data; we strip whitespace for cleanliness
    title = request.form.get("task_name", "").strip()
    description = request.form.get("description", "").strip()
    deadline_str = request.form.get("deadline", "").strip()
    author = session.get("user_nickname", "Unknown User")

    # 2. Basic validation to ensure required fields are present
    if not title or not deadline_str:
        flash("Title and Deadline are required!", "error")
        return redirect(url_for("routes.index"))

    try:
        deadline = parse_datetime_string(deadline_str)
        new_task = Task(name=title, deadline=deadline)

        if hasattr(new_task, "description"):
            new_task.description = description

        if hasattr(new_task, "author"):
            new_task.author = author

        db.session.add(new_task)
        db.session.commit()

        flash(f'Task "{title}" added successfully!', "success")

    except ValueError as ve:
        # Catch specific date parsing errors
        print(f"Date Parsing Error: {ve}")  # For terminal debugging
        flash("Invalid date format. Please use the date picker correctly.", "error")
        db.session.rollback()  # Important: undo any pending changes on error

    except Exception as e:
        # Catch all other potential database or logic errors
        print(f"General Error: {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", "error")
        db.session.rollback()

    return redirect(url_for("routes.index"))


@bp.route("/about")
def about():
    """
    Render about page.
    """
    return render_template("about.html")


@bp.route("/team")
def team():
    return render_template("team.html")
