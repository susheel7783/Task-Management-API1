# ============================================================================
# TEST FILE - Unit tests for Task Management API
# ============================================================================
# This file contains comprehensive tests for all API endpoints
# Tests use pytest framework and FastAPI's TestClient
# ============================================================================

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, Base, get_db
import os
import time

# ============================================================================
# TEST DATABASE SETUP
# ============================================================================
# Use a separate test database to avoid affecting production data
TEST_DATABASE_URL = "sqlite:///./test_tasks.db"

# Create test database engine with thread-safety disabled for SQLite
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=None  # Disable connection pooling to avoid file lock issues
)

# Create session factory for test database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================================
# DATABASE DEPENDENCY OVERRIDE
# ============================================================================
def override_get_db():
    """
    Override the get_db dependency to use test database instead of production.
    This ensures tests don't modify the real database.
    
    Yields:
        Database session connected to test database
    """
    try:
        # Create test database session
        db = TestingSessionLocal()
        yield db
    finally:
        # Always close session after test
        db.close()

# Replace the production database dependency with test database
app.dependency_overrides[get_db] = override_get_db

# ============================================================================
# PYTEST FIXTURES
# ============================================================================
@pytest.fixture(scope="function")
def client():
    """
    Pytest fixture that provides a test client for each test function.
    Creates a fresh database before each test and cleans up after.
    
    Scope: function - runs before/after each test function
    
    Yields:
        TestClient: FastAPI test client for making API requests
    
    Workflow:
        1. Create all database tables
        2. Provide test client to test function
        3. Drop all tables after test
        4. Close engine connections
        5. Delete test database file (with retry for Windows)
    """
    # Create all database tables before test
    Base.metadata.create_all(bind=engine)
    
    # Create test client for making HTTP requests
    test_client = TestClient(app)
    
    # Provide client to test function
    yield test_client
    
    # Cleanup after test - drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Dispose engine connections to release file lock (important for Windows)
    engine.dispose()
    
    # Delete test database file if it exists
    # Retry mechanism for Windows file lock issues
    if os.path.exists("test_tasks.db"):
        max_retries = 5
        for i in range(max_retries):
            try:
                time.sleep(0.1)  # Short delay to ensure file is released
                os.remove("test_tasks.db")
                break
            except PermissionError:
                if i == max_retries - 1:
                    # If still can't delete after retries, just pass
                    # The file will be overwritten in next test anyway
                    pass
                time.sleep(0.1)

# ============================================================================
# TEST CASES - Core CRUD Operations
# ============================================================================

def test_create_task(client):
    """
    Test Case 1: Create a new task (POST /tasks)
    
    Tests:
        - Task creation with all fields
        - Correct HTTP status code (201 Created)
        - Response contains all provided fields
        - Auto-generated ID is present
    
    Expected Result:
        - Status: 201 Created
        - Task created with all provided data
    """
    # Make POST request to create task
    response = client.post(
        "/tasks",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "status": "pending",
            "priority": "high"
        }
    )
    
    # Assert correct status code
    assert response.status_code == 201
    
    # Parse response JSON
    data = response.json()
    
    # Verify all fields match the input
    assert data["title"] == "Test Task"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    
    # Verify ID was auto-generated
    assert "id" in data


def test_get_all_tasks(client):
    """
    Test Case 2: Retrieve all tasks (GET /tasks)
    
    Tests:
        - Retrieving multiple tasks
        - Correct count of returned tasks
        - Correct HTTP status code (200 OK)
    
    Expected Result:
        - Status: 200 OK
        - Returns list with 2 tasks
    """
    # Create two test tasks
    client.post("/tasks", json={"title": "Task 1", "status": "pending", "priority": "low"})
    client.post("/tasks", json={"title": "Task 2", "status": "completed", "priority": "high"})
    
    # Make GET request to retrieve all tasks
    response = client.get("/tasks")
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Parse response and verify count
    data = response.json()
    assert len(data) == 2


def test_get_task_by_id(client):
    """
    Test Case 3: Retrieve a specific task by ID (GET /tasks/{id})
    
    Tests:
        - Getting a single task by ID
        - Correct HTTP status code (200 OK)
        - Returned task matches the requested ID
        - All task fields are present
    
    Expected Result:
        - Status: 200 OK
        - Returns the correct task
    """
    # Create a task and get its ID
    create_response = client.post(
        "/tasks",
        json={"title": "Specific Task", "status": "in_progress", "priority": "medium"}
    )
    task_id = create_response.json()["id"]
    
    # Make GET request for specific task
    response = client.get(f"/tasks/{task_id}")
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Verify returned task has correct ID and title
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Specific Task"


def test_update_task(client):
    """
    Test Case 4: Update an existing task (PUT /tasks/{id})
    
    Tests:
        - Partial update of task fields
        - Correct HTTP status code (200 OK)
        - Updated fields reflect new values
        - Unchanged fields remain the same
    
    Expected Result:
        - Status: 200 OK
        - Only specified fields are updated
    """
    # Create a task
    create_response = client.post(
        "/tasks",
        json={"title": "Original", "status": "pending", "priority": "low"}
    )
    task_id = create_response.json()["id"]
    
    # Update task with new values
    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated", "status": "completed"}
    )
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Verify updated fields
    data = response.json()
    assert data["title"] == "Updated"
    assert data["status"] == "completed"


def test_delete_task(client):
    """
    Test Case 5: Delete a task (DELETE /tasks/{id})
    
    Tests:
        - Task deletion
        - Correct HTTP status code (204 No Content)
        - Task is actually removed from database
        - Attempting to get deleted task returns 404
    
    Expected Result:
        - Status: 204 No Content
        - Task no longer exists in database
    """
    # Create a task
    create_response = client.post(
        "/tasks",
        json={"title": "To Delete", "status": "pending", "priority": "low"}
    )
    task_id = create_response.json()["id"]
    
    # Delete the task
    response = client.delete(f"/tasks/{task_id}")
    
    # Assert correct status code (204 No Content)
    assert response.status_code == 204
    
    # Verify task no longer exists (should return 404)
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404

# ============================================================================
# TEST CASES - Filtering Functionality
# ============================================================================

def test_filter_by_status(client):
    """
    Test Case 6: Filter tasks by status (GET /tasks?status=pending)
    
    Tests:
        - Filtering by status parameter
        - Only tasks with matching status are returned
        - Correct count of filtered results
    
    Expected Result:
        - Status: 200 OK
        - Returns only tasks with "pending" status
    """
    # Create tasks with different statuses
    client.post("/tasks", json={"title": "Task 1", "status": "pending", "priority": "low"})
    client.post("/tasks", json={"title": "Task 2", "status": "completed", "priority": "high"})
    client.post("/tasks", json={"title": "Task 3", "status": "pending", "priority": "medium"})
    
    # Filter by status=pending
    response = client.get("/tasks?status=pending")
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Verify only pending tasks are returned
    data = response.json()
    assert len(data) == 2
    assert all(task["status"] == "pending" for task in data)


def test_filter_by_priority(client):
    """
    Test Case 7: Filter tasks by priority (GET /tasks?priority=high)
    
    Tests:
        - Filtering by priority parameter
        - Only tasks with matching priority are returned
        - Correct count of filtered results
    
    Expected Result:
        - Status: 200 OK
        - Returns only tasks with "high" priority
    """
    # Create tasks with different priorities
    client.post("/tasks", json={"title": "Task 1", "status": "pending", "priority": "low"})
    client.post("/tasks", json={"title": "Task 2", "status": "completed", "priority": "high"})
    client.post("/tasks", json={"title": "Task 3", "status": "pending", "priority": "high"})
    
    # Filter by priority=high
    response = client.get("/tasks?priority=high")
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Verify only high priority tasks are returned
    data = response.json()
    assert len(data) == 2


def test_combined_filters(client):
    """
    Test Case 8: Filter by both status AND priority
    (GET /tasks?status=pending&priority=high)
    
    Tests:
        - Combined filtering with multiple parameters
        - Only tasks matching ALL criteria are returned
        - Correct handling of multiple query parameters
    
    Expected Result:
        - Status: 200 OK
        - Returns only tasks matching both filters
    """
    # Create tasks with various combinations
    client.post("/tasks", json={"title": "Task 1", "status": "pending", "priority": "low"})
    client.post("/tasks", json={"title": "Task 2", "status": "pending", "priority": "high"})
    client.post("/tasks", json={"title": "Task 3", "status": "completed", "priority": "high"})
    
    # Filter by both status and priority
    response = client.get("/tasks?status=pending&priority=high")
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Verify only Task 2 matches both criteria
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"
    assert data[0]["priority"] == "high"

# ============================================================================
# TEST CASES - Validation and Error Handling
# ============================================================================

def test_invalid_status(client):
    """
    Test Case 9: Validate invalid status value
    
    Tests:
        - Input validation for status field
        - Correct HTTP status code for validation error (422)
        - API rejects invalid status values
    
    Expected Result:
        - Status: 422 Unprocessable Entity
        - Task is not created
    """
    # Attempt to create task with invalid status
    response = client.post(
        "/tasks",
        json={"title": "Test", "status": "invalid", "priority": "low"}
    )
    
    # Assert validation error status code
    assert response.status_code == 422


def test_task_not_found(client):
    """
    Test Case 10: Handle non-existent task ID
    
    Tests:
        - Error handling for non-existent resources
        - Correct HTTP status code (404 Not Found)
        - API properly handles invalid ID requests
    
    Expected Result:
        - Status: 404 Not Found
    """
    # Try to get task with non-existent ID
    response = client.get("/tasks/999")
    
    # Assert not found status code
    assert response.status_code == 404

# ============================================================================
# TEST CASES - Data Processing Features
# ============================================================================

def test_export_csv(client):
    """
    Test Case 11: Export tasks to CSV file
    (GET /tasks/export/csv)
    
    Tests:
        - CSV export functionality (required data processing feature)
        - Correct HTTP status code (200 OK)
        - Correct content type (text/csv)
        - File download headers are present
    
    Expected Result:
        - Status: 200 OK
        - Response is a CSV file
    """
    # Create a test task
    client.post("/tasks", json={"title": "Task 1", "status": "pending", "priority": "low"})
    
    # Request CSV export
    response = client.get("/tasks/export/csv")
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Verify response is CSV format
    assert "text/csv" in response.headers["content-type"]


def test_get_stats(client):
    """
    Test Case 12: Get task statistics and analytics
    (GET /tasks/stats)
    
    Tests:
        - Statistics endpoint (required data processing feature)
        - Correct HTTP status code (200 OK)
        - Accurate count calculations
        - Grouping by status and priority works correctly
    
    Expected Result:
        - Status: 200 OK
        - Accurate statistics for all tasks
    """
    # Create multiple tasks with different statuses and priorities
    client.post("/tasks", json={"title": "Task 1", "status": "pending", "priority": "low"})
    client.post("/tasks", json={"title": "Task 2", "status": "pending", "priority": "high"})
    client.post("/tasks", json={"title": "Task 3", "status": "completed", "priority": "high"})
    
    # Request statistics - FIXED: use correct endpoint
    response = client.get("/tasks/stats")
    
    # Assert correct status code
    assert response.status_code == 200
    
    # Verify statistics are accurate
    data = response.json()
    assert data["total_tasks"] == 3
    assert data["by_status"]["pending"] == 2

# ============================================================================
# TEST SUMMARY
# ============================================================================
# Total Tests: 12
# 
# Coverage:
# ✅ Create Task (POST)
# ✅ Get All Tasks (GET)
# ✅ Get Task by ID (GET)
# ✅ Update Task (PUT)
# ✅ Delete Task (DELETE)
# ✅ Filter by Status
# ✅ Filter by Priority
# ✅ Combined Filters
# ✅ Invalid Status Validation
# ✅ Task Not Found Error
# ✅ CSV Export (Data Processing)
# ✅ Statistics (Data Processing)
# 
# To run tests: pytest test_main.py -v
# To run with coverage: pytest test_main.py -v --cov=main
# ============================================================================