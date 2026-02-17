"""
API Routes - Version 1

Main router that includes all sub-routes.
"""

from fastapi import APIRouter

from backend.api.v1.endpoints import (
    articles,
    auth,
    classify,
    enhanced_search,
    reports,
    search,
    url_classifier,
    users,
)

api_router = APIRouter()

# Include sub-routers
api_router.include_router(articles.router, prefix="/articles", tags=["Articles"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(classify.router, prefix="/classify", tags=["Classification"])
api_router.include_router(url_classifier.router, prefix="/classify/url", tags=["URL Classification"])
api_router.include_router(reports.router, prefix="/reports", tags=["Bias Reports"])
api_router.include_router(search.router, prefix="/search", tags=["Topic Search"])
api_router.include_router(enhanced_search.router, prefix="/search/enhanced", tags=["Enhanced Search"])
