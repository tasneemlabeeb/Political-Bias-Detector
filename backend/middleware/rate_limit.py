"""
Middleware for request rate limiting.
"""

import time
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window."""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier (IP or API key)
        client_id = request.client.host
        
        # Check API key in headers
        api_key = request.headers.get("X-API-Key")
        if api_key:
            client_id = f"api_key:{api_key}"
        
        current_time = time.time()
        
        # Initialize or clean up old requests
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove requests older than 1 minute and 1 hour
        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if current_time - req_time < 3600  # Keep last hour
        ]
        
        # Count requests in last minute and hour
        requests_last_minute = sum(
            1 for req_time in self.requests[client_id]
            if current_time - req_time < 60
        )
        requests_last_hour = len(self.requests[client_id])
        
        # Check limits
        if requests_last_minute >= settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "details": "Too many requests per minute",
                    "retry_after": 60,
                },
            )
        
        if requests_last_hour >= settings.RATE_LIMIT_PER_HOUR:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "details": "Too many requests per hour",
                    "retry_after": 3600,
                },
            )
        
        # Record this request
        self.requests[client_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(
            settings.RATE_LIMIT_PER_MINUTE
        )
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            settings.RATE_LIMIT_PER_MINUTE - requests_last_minute
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(
            settings.RATE_LIMIT_PER_HOUR
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            settings.RATE_LIMIT_PER_HOUR - requests_last_hour
        )
        
        return response
