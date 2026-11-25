"""
User authentication routing module.
Handles login, logout and other user authentication related functions.
"""

from flask import request, jsonify, session, redirect, url_for
from tasktracker.routes import bp  # Import unified Blueprint instance
from tasktracker.models import User


@bp.route("/register", methods=["POST"])
def register():
    """
    Handle user registration via JSON request.
    Creates a new user account with username, password, and nickname.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    nickname = data.get("nickname", "").strip()

    # Validate required fields
    if not username or not password or not nickname:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Username, password, and nickname are required",
                }
            ),
            400,
        )

    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"success": False, "message": "Username already exists"}), 409

    # Create new user
    try:
        new_user = User(username=username, nickname=nickname)
        new_user.set_password(password)

        from tasktracker import db

        db.session.add(new_user)
        db.session.commit()

        return (
            jsonify({"success": True, "message": "User registered successfully"}),
            201,
        )
    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Registration failed"}), 500


@bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login via JSON request.
    GET: Redirect to home page (for compatibility with tests)
    POST: Process login credentials
    """
    if request.method == "GET":
        return redirect(url_for("routes.index"))
    # POST method handling
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        # Save user information to session
        session["user_nickname"] = user.nickname
        return jsonify({"success": True, "nickname": user.nickname}), 200
    else:
        return jsonify({"success": False, "message": "Wrong username or password"}), 401


@bp.route("/logout")
def logout():
    """
    Clear user session and redirect to index page.
    """
    session.pop("user_nickname", None)
    return redirect(url_for("routes.index"))
