"""
SQLAlchemy database models for Task Tracker application.
"""

# from datetime import UTC, datetime
from datetime import datetime, timezone
from . import db


class Task(db.Model):
    """
    Task model representing a task with name and deadline.

    Attributes:
        id (int): Primary key identifier
        name (str): Task name (max 200 characters)
        deadline (datetime): Due date and time for the task (required)
        created_at (datetime): Timestamp when task was created
        completed (bool): Whether the task is completed
    """

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    author = db.Column(db.String(50))

    def to_dict(self):
        """
        Convert task object to dictionary for JSON serialization.
        Ensure ALL fields are included so the frontend can display them.
        """
        return {
            "id": self.id,
            "name": self.name,
            "deadline": (
                self.deadline.strftime("%Y-%m-%d %H:%M:%S") if self.deadline else None
            ),
            "description": self.description or "",
            "author": self.author or "Unknown",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed": self.completed,
        }

    def __repr__(self):
        return f"<Task {self.id}: {self.name[:20]}>"


class User(db.Model):
    """
    User model for login authentication.

    Attributes:
        id (int): Primary key identifier.
        username (str): Login username, unique.
        password_hash (str): Hashed password for secure authentication.
        nickname (str): Display name stored in session.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        """Hash and store password for this user."""
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify supplied password against stored hash."""
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
        }

    def __repr__(self):
        return f"<User {self.username}>"


def init_default_users():
    """Initialize default login users when the users table is empty."""
    if User.query.first() is None:
        admin = User(username="admin", nickname="admin")
        admin.set_password("123")

        user1 = User(username="user1", nickname="user1")
        user1.set_password("666")

        user2 = User(username="user2", nickname="user2")
        user2.set_password("222")
        db.session.add(user2)

        user3 = User(username="user3", nickname="user3")
        user3.set_password("333")
        db.session.add(user3)

        db.session.add_all([admin, user1, user2, user3])
        db.session.commit()
