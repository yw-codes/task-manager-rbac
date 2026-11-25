"""
Unified routing module package.
Using a unified Blueprint instance to ensure URL structure remains unchanged.
"""

from flask import Blueprint

# Create a unified Blueprint instance, shared by all routing modules
bp = Blueprint("routes", __name__)

# Import all routing modules using absolute imports to avoid circular imports
# These imports ensure route decorators are executed and registered with bp
import tasktracker.routes.auth_routes  # noqa: F401, E402
import tasktracker.routes.page_routes  # noqa: F401, E402
import tasktracker.routes.task_api_routes  # noqa: F401, E402
import tasktracker.routes.utils  # noqa: F401, E402
