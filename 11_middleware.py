"""
FastAPI Advanced Level - File 11: Middleware and CORS
==================================================

This file covers advanced middleware concepts in FastAPI including:
- Custom middleware creation
- CORS (Cross-Origin Resource Sharing) configuration
- Compression middleware
- Rate limiting middleware
- Logging and monitoring middleware
- Request/Response processing middleware
- Security middleware
- Error handling middleware

Middleware in FastAPI allows you to process requests and responses at a global level,
adding functionality that runs before and after your route handlers.
"""

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
import time
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import uuid
from collections import defaultdict

# Configure logging for middleware
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Advanced Middleware Demo",
    description="Comprehensive middleware implementation examples",
    version="1.0.0"
)

# ==================================================
# 1. CORS MIDDLEWARE CONFIGURATION
# ==================================================

# CORS allows web applications running at one domain to access resources from another domain
# This is essential for modern web applications with separate frontend and backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins like ["https://myapp.com"]
    allow_credentials=True,  # Allow cookies and auth headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose custom headers to the client
)

# ==================================================
# 2. GZIP COMPRESSION MIDDLEWARE
# ==================================================

# Automatically compress responses to reduce bandwidth usage
# This is especially important for APIs that return large JSON responses
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # Only compress responses larger than 1000 bytes
)

# ==================================================
# 3. TRUSTED HOST MIDDLEWARE
# ==================================================

# Security middleware to prevent Host header attacks
# This validates that the Host header matches expected values
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["127.0.0.1", "localhost", "*.example.com"]
)

# ==================================================
# 4. SESSION MIDDLEWARE
# ==================================================

# Add session support for stateful operations
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-here-make-it-strong-and-random",
    max_age=3600,  # Session expires after 1 hour
    https_only=False  # Set to True in production with HTTPS
)

# ==================================================
# 5. CUSTOM TIMING MIDDLEWARE
# ==================================================

class TimingMiddleware(BaseHTTPMiddleware):
    """
    Custom middleware to measure request processing time
    This helps identify slow endpoints and performance bottlenecks
    """
    
    async def dispatch(self, request: Request, call_next):
        # Record the start time when request arrives
        start_time = time.time()
        
        # Add a unique request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log incoming request
        logger.info(f"Request {request_id}: {request.method} {request.url}")
        
        # Process the request through the application
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add timing information to response headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log response information
        logger.info(f"Request {request_id} completed in {process_time:.4f}s with status {response.status_code}")
        
        return response

# Add the custom timing middleware to the app
app.add_middleware(TimingMiddleware)

# ==================================================
# 6. RATE LIMITING MIDDLEWARE
# ==================================================

# Simple in-memory rate limiter (use Redis in production)
rate_limit_storage: Dict[str, List[datetime]] = defaultdict(list)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse
    Limits requests per IP address within a time window
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Maximum number of calls
        self.period = period  # Time period in seconds
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP address
        client_ip = request.client.host
        current_time = datetime.now()
        
        # Clean old entries for this IP
        cutoff_time = current_time - timedelta(seconds=self.period)
        rate_limit_storage[client_ip] = [
            timestamp for timestamp in rate_limit_storage[client_ip]
            if timestamp > cutoff_time
        ]
        
        # Check if rate limit exceeded
        if len(rate_limit_storage[client_ip]) >= self.calls:
            # Return rate limit exceeded response
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.calls} requests per {self.period} seconds allowed",
                    "retry_after": self.period
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # Add current request to rate limit storage
        rate_limit_storage[client_ip].append(current_time)
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = self.calls - len(rate_limit_storage[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int((current_time + timedelta(seconds=self.period)).timestamp()))
        
        return response

# Add rate limiting middleware (100 requests per minute)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# ==================================================
# 7. SECURITY HEADERS MIDDLEWARE
# ==================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    These headers help protect against common web vulnerabilities
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"  # Prevent MIME type sniffing
        response.headers["X-Frame-Options"] = "DENY"  # Prevent clickjacking
        response.headers["X-XSS-Protection"] = "1; mode=block"  # XSS protection
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # HTTPS only
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"  # Control referrer information
        response.headers["Content-Security-Policy"] = "default-src 'self'"  # Content Security Policy
        
        return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# ==================================================
# 8. REQUEST/RESPONSE LOGGING MIDDLEWARE
# ==================================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware for debugging and monitoring
    Logs request details, response status, and any errors
    """
    
    async def dispatch(self, request: Request, call_next):
        # Log request details
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            # Read request body for logging (be careful with large payloads)
            body = await request.body()
            if body:
                try:
                    request_body = json.loads(body.decode())
                except json.JSONDecodeError:
                    request_body = body.decode()[:500]  # Truncate large bodies
        
        # Log request information
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        if request_body:
            logger.info(f"Body: {request_body}")
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Log successful response
            logger.info(f"Response: {response.status_code}")
            
            return response
            
        except Exception as e:
            # Log any errors that occur
            logger.error(f"Error processing request: {str(e)}")
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An error occurred while processing your request",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# ==================================================
# 9. AUTHENTICATION MIDDLEWARE
# ==================================================

# JWT token verification (simplified for demo)
security = HTTPBearer()

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware to protect certain routes
    Checks for valid JWT tokens in protected paths
    """
    
    # Define which paths require authentication
    PROTECTED_PATHS = ["/protected", "/admin"]
    
    async def dispatch(self, request: Request, call_next):
        # Check if this path requires authentication
        path = request.url.path
        requires_auth = any(path.startswith(protected) for protected in self.PROTECTED_PATHS)
        
        if requires_auth:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Authentication required",
                        "message": "Please provide a valid Bearer token"
                    }
                )
            
            # Extract and validate token (simplified validation)
            token = auth_header.split(" ")[1]
            if not self._validate_token(token):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Invalid token",
                        "message": "The provided token is invalid or expired"
                    }
                )
            
            # Add user info to request state
            request.state.user = self._get_user_from_token(token)
        
        return await call_next(request)
    
    def _validate_token(self, token: str) -> bool:
        """
        Validate JWT token (simplified for demo)
        In production, use proper JWT validation with secret key
        """
        # For demo purposes, accept any token that starts with "valid_"
        return token.startswith("valid_")
    
    def _get_user_from_token(self, token: str) -> dict:
        """
        Extract user information from token (simplified for demo)
        """
        return {
            "id": 1,
            "username": "demo_user",
            "email": "demo@example.com"
        }

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# ==================================================
# 10. DEMO ROUTES
# ==================================================

@app.get("/")
async def root():
    """
    Basic route to test middleware functionality
    All middleware will process this request
    """
    return {
        "message": "Hello World!",
        "timestamp": datetime.now().isoformat(),
        "note": "This response went through all middleware layers"
    }

@app.get("/large-data")
async def large_data():
    """
    Route that returns large data to test compression middleware
    """
    # Generate large response to test GZip compression
    large_list = [{"id": i, "data": f"Large data item {i}" * 10} for i in range(100)]
    return {
        "message": "Large data response",
        "data": large_list,
        "size": len(large_list)
    }

@app.get("/slow-endpoint")
async def slow_endpoint():
    """
    Intentionally slow endpoint to test timing middleware
    """
    # Simulate slow processing
    await asyncio.sleep(2)
    return {
        "message": "This endpoint took 2 seconds to process",
        "note": "Check the X-Process-Time header"
    }

@app.post("/session-demo")
async def session_demo(request: Request):
    """
    Demonstrate session middleware functionality
    """
    # Access session data
    session_data = request.session.get("visits", 0)
    request.session["visits"] = session_data + 1
    
    return {
        "message": "Session demo",
        "visits": request.session["visits"],
        "session_id": request.session.get("session_id", "new")
    }

@app.get("/protected/data")
async def protected_data(request: Request):
    """
    Protected route that requires authentication
    Use: Authorization: Bearer valid_token_123
    """
    user = request.state.user
    return {
        "message": "Protected data accessed successfully",
        "user": user,
        "data": "This is sensitive information"
    }

@app.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    """
    Admin-only route
    Use: Authorization: Bearer valid_admin_token
    """
    user = request.state.user
    return {
        "message": "Admin dashboard",
        "user": user,
        "admin_data": ["User management", "System stats", "Configuration"]
    }

@app.get("/rate-limit-test")
async def rate_limit_test():
    """
    Test rate limiting by calling this endpoint rapidly
    """
    return {
        "message": "Rate limit test",
        "note": "Call this endpoint repeatedly to test rate limiting",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/error-test")
async def error_test():
    """
    Test error handling middleware
    """
    # Intentionally raise an error
    raise Exception("This is a test error")

@app.get("/middleware-info")
async def middleware_info(request: Request):
    """
    Display information about request processing
    """
    return {
        "message": "Middleware information",
        "request_id": getattr(request.state, 'request_id', 'not available'),
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "headers": dict(request.headers),
        "middleware_layers": [
            "CORSMiddleware",
            "GZipMiddleware",
            "TrustedHostMiddleware",
            "SessionMiddleware",
            "TimingMiddleware",
            "RateLimitMiddleware",
            "SecurityHeadersMiddleware",
            "LoggingMiddleware",
            "AuthMiddleware"
        ]
    }

# ==================================================
# 11. MIDDLEWARE TESTING UTILITIES
# ==================================================

@app.get("/test-compression")
async def test_compression():
    """
    Test compression with a large response
    """
    # Create a large response to test compression
    data = "This is a test string that will be repeated many times. " * 1000
    return {
        "message": "Compression test",
        "data": data,
        "size": len(data),
        "note": "This response should be compressed due to its size"
    }

@app.get("/test-cors")
async def test_cors():
    """
    Test CORS headers
    """
    return {
        "message": "CORS test",
        "note": "Check response headers for CORS configuration",
        "cors_headers": [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
    }

"""
How to Run This Example:
1. Save this file as 11_middleware.py
2. Install required dependencies: pip install fastapi uvicorn
3. Run: uvicorn 11_middleware:app --reload
4. Test different endpoints:
   - http://127.0.0.1:8000/docs (Interactive API documentation)
   - http://127.0.0.1:8000/ (Basic route)
   - http://127.0.0.1:8000/large-data (Test compression)
   - http://127.0.0.1:8000/slow-endpoint (Test timing)
   - http://127.0.0.1:8000/protected/data (Test auth - use Bearer valid_token_123)
   - http://127.0.0.1:8000/rate-limit-test (Test rate limiting)

Testing Authentication:
curl -H "Authorization: Bearer valid_token_123" http://127.0.0.1:8000/protected/data

Testing Rate Limiting:
Run multiple rapid requests to see rate limiting in action

Key Learning Points:
1. Middleware executes in the order it's added to the app
2. Each middleware can modify requests and responses
3. Middleware is perfect for cross-cutting concerns (auth, logging, timing)
4. Custom middleware gives you full control over request processing
5. Built-in middleware handles common requirements (CORS, compression)
6. Always consider performance impact of middleware
7. Use middleware for security, monitoring, and debugging
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 