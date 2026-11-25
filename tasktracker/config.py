"""
Database configuration for Task Tracker application.
"""

import os

# Get the base directory of the project
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    """Base configuration class."""

    # Secret key for session management (should be changed in production)
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # SQLite database configuration - absolute path
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f'sqlite:///{os.path.join(basedir, "instance", "tasktracker.db")}'
    )

    # Disable modification tracking to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Enable foreign key constraints for SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}

    @staticmethod
    def ensure_instance_dir():
        """Ensure the instance directory exists."""
        instance_dir = os.path.join(basedir, "instance")
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir, exist_ok=True)
