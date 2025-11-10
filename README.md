# Task Management API

## Overview

The Task Management API is a RESTful service built with FastAPI and SQLAlchemy. It provides endpoints for managing tasks, including CRUD operations, filtering, CSV export, and analytics. The project follows a layered architecture with clear separation of concerns, making it maintainable and scalable.

---

## Features

- **CRUD Operations**: Create, Read, Update, and Delete tasks.
- **Filtering**: Filter tasks by status and priority.
- **CSV Export**: Export all tasks as a CSV file.
- **Analytics**: Get task statistics grouped by status and priority.
- **Validation**: Input validation using Pydantic models.
- **Layered Architecture**: Separation of routes, services, and repositories.
- **Enum Usage**: Replace magic strings with enums for status and priority.

---

## Project Structure

```
task-management-api/
├── main.py              # FastAPI app initialization
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── tasks.py  # Route handlers
│   ├── models/
│   │   ├── database.py       # SQLAlchemy models and DB setup
│   │   ├── domain.py         # Pydantic models
│   │   └── enums.py          # TaskStatus and TaskPriority enums
│   ├── repositories/
│   │   └── task_repository.py  # Repository layer
│   ├── services/
│   │   └── task_service.py     # Business logic
├── requirements.txt     # Dependencies
├── test_main.py         # Unit tests
├── tasks.db             # SQLite database (runtime-generated)
└── README.md            # Documentation
```

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/susheel7783/Task-Management-API1.git
   cd Task-Management-API
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Access the API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## Usage

### Endpoints

- **Create Task**: `POST /tasks`
- **Get All Tasks**: `GET /tasks`
- **Get Task by ID**: `GET /tasks/{task_id}`
- **Update Task**: `PUT /tasks/{task_id}`
- **Delete Task**: `DELETE /tasks/{task_id}`
- **Export Tasks as CSV**: `GET /tasks/export/csv`
- **Get Task Statistics**: `GET /tasks/stats`

### Example Request

**Create a Task**:
```bash
curl -X POST "http://127.0.0.1:8000/tasks" \
-H "Content-Type: application/json" \
-d '{"title": "New Task", "description": "Description here", "status": "pending", "priority": "medium"}'
```

---

## Testing

Run the unit tests using pytest:
```bash
pytest test_main.py -v
```

To check test coverage:
```bash
pytest test_main.py -v --cov=main
```

## License

This project is licensed under the MIT License.
