# Complexity Refactoring Report: Task Tracker API Routes

## Executive Summary

This report analyzes the refactoring of the Task Tracker API routes from Sprint 1 to Sprint 2, focusing on complexity management principles discussed in Lecture 7.2. The refactoring transformed a monolithic `handle_tasks_api()` function into a modular, maintainable architecture with clear separation of concerns.

## 1. Essential vs Accidental Complexity

### Essential Complexity: User Permission Management
**What changed**: The inherent complexity of user permission management remained essential but was better encapsulated.

**Before refactoring** (accidental + essential mixing):
```python
# Lines 26-47 in task_api_routes_before_fix.py
if current_user == "admin":
    if sort_order == "desc":
        tasks = Task.query.order_by(Task.deadline.desc()).all()
    else:
        tasks = Task.query.order_by(Task.deadline.asc()).all()
elif current_user:
    if sort_order == "desc":
        tasks = Task.query.filter_by(author=current_user).order_by(Task.deadline.desc()).all()
    else:
        tasks = Task.query.filter_by(author=current_user).order_by(Task.deadline.asc()).all()
else:
    tasks = []
```

**After refactoring** (essential complexity isolated):
```python
# Lines 13-23 in task_api_routes.py
def get_authorized_tasks_query(current_user):
    if current_user == "admin":
        return Task.query
    elif current_user:
        return Task.query.filter_by(author=current_user)
    return None
```

**Why it matters**: User permission logic is inherently complex (admin sees all, users see own, guests see none). The refactoring isolates this essential complexity into a single function with clear input/output, making it testable and reusable.

### Accidental Complexity: Duplicated Error Handling
**What changed**: Eliminated duplicated try-catch blocks across multiple routes.

**Before refactoring** (accidental complexity in 4 locations):
```python
# Lines 67-84 in task_api_routes_before_fix.py (create)
# Lines 132-152 in task_api_routes_before_fix.py (update)  
# Lines 99-116 in task_api_routes_before_fix.py (status update)
# Lines 155-176 in task_api_routes_before_fix.py (bulk delete)

try:
    # database operations
    db.session.commit()
except ValueError:
    return jsonify({"error": "Invalid date format"}), 400
except Exception as e:
    db.session.rollback()
    return jsonify({"error": str(e)}), 500
```

**After refactoring** (accidental complexity eliminated):
```python
# Lines 53-69 in task_api_routes.py
def handle_database_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    return wrapper
```

**Why it matters**: The error handling pattern was identical across routes—pure accidental complexity. The decorator DRYs (Don't Repeat Yourself) the code, reducing maintenance overhead and ensuring consistent error responses.

## 2. Coupling/Cohesion Improvements

### Increased Cohesion: Single Responsibility Principle
**Before refactoring** (low cohesion):
- `handle_tasks_api()`: 52 lines doing GET logic, POST logic, validation, error handling, session management
- Violated Single Responsibility Principle: one function handled request parsing, authorization, query building, sorting, validation, and response formatting

**After refactoring** (high cohesion):
- `get_tasks()`: 18 lines focused only on GET request flow
- `create_task()`: 17 lines focused only on POST request flow  
- `get_authorized_tasks_query()`: 11 lines focused only on permission logic
- `apply_sorting()`: 7 lines focused only on sorting logic
- `validate_task_data()`: 15 lines focused only on input validation

**Boundary clarified**: Separated UI routing layer (Flask routes) from business logic layer (helper functions). Routes now delegate to specialized functions rather than implementing logic directly.

### Reduced Coupling: Dependency Inversion
**Before refactoring** (tight coupling):
```python
# Direct coupling between route and database query details
tasks = Task.query.filter_by(author=current_user).order_by(Task.deadline.desc()).all()
```

**After refactoring** (loose coupling):
```python
# Route depends on abstraction (function interface)
query = get_authorized_tasks_query(current_user)
query = apply_sorting(query, sort_order)
tasks = query.all()
```

**Why it matters**: Routes now depend on function interfaces rather than SQLAlchemy implementation details. This makes the code more testable (can mock `get_authorized_tasks_query`) and flexible (can change database implementation without affecting routes).

## 3. Cyclomatic Complexity Analysis

### Methodology
Cyclomatic complexity V(G) measures the number of linearly independent paths through a program's source code. We calculate it using the control flow graph method: V(G) = e - n + 2, where e is the number of edges and n is the number of nodes.

### Before Refactoring: `handle_tasks_api()`
**Control Flow Graph Analysis**:
- **Nodes (n)**: 24 logical points including function entry, decision points, assignments, returns, and exits
- **Edges (e)**: 33 connections representing all possible execution paths
- **Calculation**: V(G) = 33 - 24 + 2 = 11


### After Refactoring: Distributed Complexity

**`get_tasks()` function**:
- **Nodes**: 8 (function entry, query check, return paths)
- **Edges**: 9
- **V(G)**: 9 - 8 + 2 = 3

**`create_task()` function** (with decorator):
- **Nodes**: 10 (including validation checks and return paths)
- **Edges**: 12
- **V(G)**: 12 - 10 + 2 = 4

**Helper functions**:
- `get_authorized_tasks_query()`: V(G) = 3
- `apply_sorting()`: V(G) = 2  
- `validate_task_data()`: V(G) = 4
- `handle_database_errors()` decorator: V(G) = 3

### Complexity Reduction Analysis

| Component | Before V(G) | After V(G) | Reduction |
|-----------|------------|------------|-----------|
| Main API logic | 11 | 3 + 4 = 7 | 36% |
| Distributed to helpers | - | 3 + 2 + 4 + 3 = 12 | - |
| **Total complexity** | 11 | **Max individual V(G)** = 4 | **64% per function** |

**Critical insight**: While the total logical paths remain similar (11 before vs 7+12=19 distributed), the maximum complexity per function dropped from 11 to 4. This is the key improvement: each function now has V(G) ≤ 4, which is within the recommended limit for maintainability and testability.

**Testability impact**: Functions with V(G) ≤ 4 require ≤ 4 test cases to achieve branch coverage, compared to 11 test cases for the original function. This dramatically reduces testing effort and improves confidence in code correctness.

## 4. Testing Coverage Verification

**Test Execution Results** (from `pytest -v`):
- **Total tests**: 47 tests
- **Pass rate**: 100% (47 passed, 0 failed)
- **Overall coverage**: 93%
- **`task_api_routes.py` coverage**: 95% (125 statements, 6 missed)

**Key test categories verified**:
1. **Task creation and validation tests** - `test_add_task_api_invalid_date`, `test_add_task_form_success`
2. **Permission-based filtering tests** - Verified through route testing with admin/user sessions  
3. **Sorting functionality tests** - `test_task_sorting_asc_and_desc`
4. **Error handling tests** - `test_api_tasks_errors`, `test_api_tasks_general_exception`
5. **Bulk operation tests** - `test_bulk_delete_success`, `test_bulk_delete_partial`
6. **Filter functionality tests** - `test_filter_completed`, `test_filter_pending`, `test_combined_filters`

**Coverage Details for Refactored Components**:
| File | Statements | Missed | Coverage |
|------|------------|---------|----------|
| `task_api_routes.py` | 125 | 6 | 95% |
| `routes/utils.py` | 26 | 0 | 100% |
| `tests/test_routes.py` | 236 | 0 | 100% |

**Testability Improvements Validated**:
1. **Isolated unit tests**: `test_filter_completed`, `test_filter_pending` test utility functions without Flask context
2. **Mockability**: Decorator pattern tested through `test_api_tasks_general_exception`
3. **Edge case coverage**: `test_edit_task_invalid_data` validates error handling for malformed inputs
4. **Reduced test complexity**: Each refactored function requires ≤ 4 test cases, verified by focused test methods


## References

**Git History & MR Links**:
- Main refactoring MR: coursework/comp9820/26t1/groups/T09A-C/tasktracker!46
- Complexity Analysis issue:coursework/comp9820/26t1/groups/T09A-C/tasktracker#42


**Related Commits**:
- `db80d019772c7ca7bcf81a21707d0faf9d9a33fd` - fix server error caused by wrong function name 
- `0f1a9907d07b7dc3d72c3c258710624c692b19ce` - get changes in main branch
- `3c2097ac16630750ba2c7a3faeb1de433ec1608a` - flake code style fix
- `ab689b22d36fa01eb5dcabcbf6228e8db04cb69b` - decorator set
- `cd1a2240fc8547472f51f3de0beb89676926577c` - code style details repair
- `52378190afd19e341b2565d13a5c2efd4fbbc069` - complexity reduction on handle_task_api()


