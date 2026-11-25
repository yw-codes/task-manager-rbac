# Developer Workflow

This document describes the standard workflow for developers working on the TaskTracker project.

## 1. Setup the Project

Clone the repository:

```
git clone <repository-url>
cd tasktracker
```

Create a virtual environment:

```
python -m venv .venv
```

Activate it:

Windows:

```
.venv\Scripts\activate
```

Install dependencies:

```
py -m pip install -r requirements.txt
```

Install pre-commit hooks:

```
pre-commit install
```

---

# 2. Project Structure

```
tasktracker/
│
├── tasktracker/        # Python package
│   ├── __init__.py
│   ├── routes.py
│   └── templates/
│
├── tests/              # Test suite
│   └── test_routes.py
│
├── requirements.txt
├── pytest.ini
├── .flake8
├── .pre-commit-config.yaml
└── .github/workflows/ci.yml
```

---

# 3. Running the Application

Start the Flask server:

```
flask --app tasktracker run
```

The application will run at:

```
http://127.0.0.1:5000
```

---


# 4. Database Migration Workflow

The project uses Flask-Migrate to manage database schema changes.
Do not use db.create_all(), manually delete the database or Do NOT commit .db files.

### 4.1 Initial Setup (First Time Only)


After cloning the project, initialize the database:

```

flask --app tasktracker db upgrade

```

This will:

- Create the database file (if not present)

- Apply all existing migrations

- Set up the correct schema


### 4.2 When Changing the Database Model

Whenever you modify models.py (e.g., add/remove columns), follow these steps:

- Step 1 — Generate migration

```

flask --app tasktracker db migrate -m "Describe your change"

```
- Step 2 — Apply migration

```

flask --app tasktracker db upgrade

```

Example

If you add a new field:

description = db.Column(db.String(500))

Run:

```

flask --app tasktracker db migrate -m "Add description to task"
flask --app tasktracker db upgrade

```

### 4.3 Pulling Changes from Repository

If you pull changes that include migrations:

```
git pull
flask --app tasktracker db upgrade

```

This ensures your local database matches the latest schema.

# 5. Development Workflow

When implementing a new feature or bug fix, follow this process.

### Step 1 — Write or update code

Modify the relevant files in:

```
tasktracker/
tests/
```

---

### Step 2 — Format the code

```
black .
```

---

### Step 3 — Run lint checks

```
flake8 .
```

Fix any issues reported by flake8.

---

### Step 4 — Run tests

```
pytest
```

All tests must pass before committing.

---

### Step 5 — Commit changes

```
git add .
git commit -m "Describe the change"
```

Pre-commit will automatically run:

```
black
flake8
```

If checks fail, the commit will be rejected.

---

### Step 6 — Push changes

```
git push
```

---

# 6. Continuous Integration (CI)

After pushing, the GitHub Actions CI workflow will run automatically.

The pipeline performs:

1. Dependency installation
2. Lint checks using flake8
3. Test execution using pytest

If any step fails, the pipeline will fail.

---

# 7. Standard Development Cycle

Typical developer loop:

```
write code
black .
flake8 .
pytest
flask db migrate -m "message" (if needed)
flask db upgrade (if needed)
git add
git commit
git push
```

CI will verify the changes automatically.
