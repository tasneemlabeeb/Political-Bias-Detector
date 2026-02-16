"""
Authentication Endpoints

Stub endpoints for authentication (to be implemented).
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login():
    """Login endpoint (stub)."""
    return {"message": "Authentication not yet implemented"}


@router.post("/logout")
async def logout():
    """Logout endpoint (stub)."""
    return {"message": "Authentication not yet implemented"}
