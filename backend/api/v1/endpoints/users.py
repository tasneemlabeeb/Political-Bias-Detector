"""
Users Endpoints

Stub endpoints for user management (to be implemented).
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """Get current user (stub)."""
    return {"message": "User management not yet implemented"}
