# Task Tracker – Flask Task Management App with Per-User Access Control

A web app for student teams to create, track and complete project tasks. Users register and log in;
an **admin** sees and manages every task, while **standard users** can only create, view, edit and delete their own.
Features include task descriptions with automatic authorship, completion tracking, sorting by deadline,
bulk delete, search and filtering.

Group project for UNSW COMP9820 (2026), built by a team of five over three Agile sprints.

## My contribution

I worked as a software engineer and as the team's *Customer* (product owner):

- **Authentication and sessions** – registration, login and logout end to end, with sessions that persist across page refreshes.
- **Per-user access control** – admin vs standard-user views, with tasks filtered on the server so a standard user cannot reach another user's data.
- **Task authorship** – added task descriptions and automatic author mapping from the logged-in user.
- **UI and validation** – real-time form validation with clear error messages, and consistent styling across pages.
- **Testing** – pytest cases for login, wrong or empty credentials, permission boundaries and author integrity.
- **Requirements** – user stories and acceptance criteria (see [`docs/Yu-userstory.md`](docs/Yu-userstory.md)), and code review of teammates' merge requests.

## Tech stack

- **Language / runtime**: Python 3.11+
- **Framework / libraries**: Flask 3.0.0, Flask-SQLAlchemy, Flask-Migrate, Jinja2
- **Persistence**: SQLite database with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Testing**: pytest, pytest-cov, flake8
- **Code quality**: black, pre-commit

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (for version control)
- Windows/macOS/Linux with terminal access

## How to run locally

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd tasktracker
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database** (tables are created automatically on first run):
   ```bash
   # The database will be created automatically when you run the application
   ```

5. **Run the application**:
   ```bash
   python run.py
   ```
   or
   ```bash
   flask run
   ```

6. **Access the application**:
   Open your browser and navigate to `http://localhost:5001`

**Default login credentials**:
- Admin: username `admin`, password `123`
- Regular users: `user1`/`666`, `user2`/`222`, `user3`/`333`

## How to run tests and checks

**Run all tests with coverage**:
```bash
pytest -v
```

**Run specific test categories**:
```bash
# Run route tests only
pytest tests/test_routes.py -v

# Run app tests only
pytest test/test_app.py -v

# Run search functionality tests
pytest test/test_search.py -v
```

**Code quality checks**:
```bash
# Linting with flake8
flake8 .

# Code formatting check with black
black --check .

# Run pre-commit hooks
pre-commit run --all-files
```

**Generate coverage report**:
```bash
pytest --cov=tasktracker --cov-report=html
# Open htmlcov/index.html in browser to view detailed coverage
```

## Continuous integration

GitHub Actions runs `flake8` and the full pytest suite on every push (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
The suite has 47 tests with 94% line coverage. The original project ran the same checks on GitLab CI.

## Repository layout

This repository is organised as follows:

- `tasktracker/` — main Flask application package, including routes, models, templates, static assets, and configuration.
- `tasktracker/routes/` — route modules for page rendering, authentication, and task API behaviour.
- `tasktracker/templates/` — Jinja HTML templates used by the web interface.
- `tasktracker/static/` — CSS and image assets used by the frontend.
- `tests/` — main pytest suite for route and integration-style backend testing.
- `test/` — additional pytest files covering app behaviour, search, UI behaviour, and persistence flows.
- `migrations/` — Flask-Migrate/Alembic migration files for database schema changes.
- `docs/` — complexity/refactoring report and user story.
- `instance/` — local runtime data such as the SQLite database created during development.

## Team

Built by COMP9820 team T09A-C. This repository is a copy of the team's final code, published here as part of my portfolio;
the original development history lives in the course's GitLab instance.
