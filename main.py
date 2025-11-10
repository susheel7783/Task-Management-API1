# ============================================================================
# IMPORTS - All required libraries and modules
# ============================================================================
from fastapi import FastAPI
from app.api.v1.endpoints import tasks as tasks_router

# ============================================================================
# FASTAPI APPLICATION - Main application instance
# ============================================================================
app = FastAPI(
    title="Task Management API",
    description="A REST API for managing tasks with filtering and analytics",
    version="1.0.0"
)

# Include routes from the new endpoints module
app.include_router(tasks_router.router)


@app.get("/")
def root():
    """
    Root endpoint - provides basic API information.
    Returns: Dictionary with API details and available endpoints.
    """
    return {
        "message": "Task Management API",
        "version": "1.0.0",
        "docs": "/docs",
    }