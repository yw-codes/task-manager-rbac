from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from flask import session

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    """
    Application factory function to create and configure Flask app.

    Args:
        config_class: Configuration class to use

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance directory exists
    config_class.ensure_instance_dir()

    # Initialize extensions with app
    db.init_app(app)

    # ✅ MUST be before migrate.init_app
    from . import models  # noqa: F401

    migrate.init_app(app, db)

    # Register blueprints/routes
    from .routes import bp

    app.register_blueprint(bp)

    @app.context_processor
    def inject_user():
        return dict(current_user=session.get("user_nickname"))

    # Create database tables if they don't exist and seed default users
    with app.app_context():
        db.create_all()
        from .models import init_default_users

        init_default_users()

    return app


# Create default app instance
app = create_app()
