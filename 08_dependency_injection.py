"""
🔗 FastAPI Dependency Injection - Reusable Components and Logic

This file teaches you everything about FastAPI's dependency injection system:
- Basic dependencies and Depends()
- Dependency hierarchy and sub-dependencies
- Dependency caching and scoping
- Class-based dependencies
- Advanced dependency patterns

Run this file with: uvicorn 08_dependency_injection:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, status, Header, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime, timedelta
import time
import hashlib
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="FastAPI Dependency Injection Tutorial",
    description="Master dependency injection patterns and reusable components",
    version="1.0.0"
)

# LINE-BY-LINE EXPLANATION OF DEPENDENCY BASICS:

# 1. SIMPLE FUNCTION DEPENDENCIES
def get_current_timestamp() -> datetime:
    """
    Simple dependency that returns current timestamp.
    
    This is the most basic type of dependency - a function that returns a value.
    It can be injected into any endpoint that needs the current timestamp.
    
    Returns:
        datetime: Current timestamp
    """
    return datetime.now()

def get_user_agent(user_agent: str = Header(None)) -> Optional[str]:
    """
    Dependency that extracts User-Agent header.
    
    This dependency demonstrates how to extract and process request headers.
    It can be reused across multiple endpoints that need user agent information.
    
    Args:
        user_agent (str): User-Agent header from request
        
    Returns:
        Optional[str]: User agent string or None
    """
    return user_agent

def get_request_id(request: Request) -> str:
    """
    Dependency that generates a unique request ID.
    
    This dependency demonstrates how to access the request object
    and generate unique identifiers for tracking and logging.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        str: Unique request identifier
    """
    # Generate unique ID based on request details
    unique_string = f"{request.method}{request.url}{time.time()}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:8]

# 2. DEPENDENCY WITH PARAMETERS
def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return")
) -> Dict[str, int]:
    """
    Dependency for pagination parameters.
    
    This dependency encapsulates pagination logic and validation.
    It can be reused across all endpoints that need pagination.
    
    Args:
        skip (int): Number of items to skip
        limit (int): Number of items to limit
        
    Returns:
        Dict[str, int]: Pagination parameters
    """
    return {"skip": skip, "limit": limit}

# 3. CACHED DEPENDENCIES
@lru_cache()
def get_application_settings() -> Dict[str, Any]:
    """
    Cached dependency for application settings.
    
    The @lru_cache decorator ensures this function is only called once
    and the result is cached for subsequent calls. This is useful for
    expensive operations like reading configuration files.
    
    Returns:
        Dict[str, Any]: Application settings
    """
    # Simulate expensive operation (e.g., reading config file)
    time.sleep(0.1)
    
    return {
        "app_name": "FastAPI Tutorial",
        "version": "1.0.0",
        "debug": True,
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_origins": ["localhost", "127.0.0.1"],
        "cache_ttl": 300  # 5 minutes
    }

# 4. CLASS-BASED DEPENDENCIES
class DatabaseConnection:
    """
    Class-based dependency for database connections.
    
    Class-based dependencies are useful for maintaining state
    and providing more complex functionality.
    """
    
    def __init__(self):
        self.connection_count = 0
        self.last_connection = None
    
    def get_connection(self) -> Dict[str, Any]:
        """
        Simulate getting a database connection.
        
        Returns:
            Dict[str, Any]: Database connection info
        """
        self.connection_count += 1
        self.last_connection = datetime.now()
        
        logger.info(f"Database connection #{self.connection_count} established")
        
        return {
            "connection_id": f"conn_{self.connection_count}",
            "connected_at": self.last_connection,
            "status": "active"
        }

# Create instance (this will be shared across requests)
database = DatabaseConnection()

class UserService:
    """
    Service class for user-related operations.
    
    This demonstrates how to create service classes that can be
    injected as dependencies.
    """
    
    def __init__(self, db_connection: Dict[str, Any] = Depends(database.get_connection)):
        self.db = db_connection
        self.users_cache = {}
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID (with caching)."""
        if user_id in self.users_cache:
            return self.users_cache[user_id]
        
        # Simulate database query
        user = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": datetime.now(),
            "connection_id": self.db["connection_id"]
        }
        
        self.users_cache[user_id] = user
        return user
    
    def get_user_count(self) -> int:
        """Get total user count."""
        # Simulate database query
        return len(self.users_cache) + 100  # Simulate 100 existing users

# 5. DEPENDENCY WITH VALIDATION
def validate_api_key(api_key: str = Header(None, alias="X-API-Key")) -> str:
    """
    Dependency that validates API key.
    
    This dependency demonstrates how to perform validation
    and raise exceptions when validation fails.
    
    Args:
        api_key (str): API key from X-API-Key header
        
    Returns:
        str: Validated API key
        
    Raises:
        HTTPException: When API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Simulate API key validation
    valid_keys = ["secret-key-123", "admin-key-456", "user-key-789"]
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return api_key

# 6. DEPENDENCY WITH SUB-DEPENDENCIES
def get_user_permissions(
    api_key: str = Depends(validate_api_key),
    user_service: UserService = Depends(UserService)
) -> List[str]:
    """
    Dependency that determines user permissions based on API key.
    
    This dependency demonstrates sub-dependencies - it depends on
    both validate_api_key and UserService dependencies.
    
    Args:
        api_key (str): Validated API key
        user_service (UserService): User service instance
        
    Returns:
        List[str]: List of user permissions
    """
    # Determine permissions based on API key
    permissions_map = {
        "secret-key-123": ["read", "write", "delete"],
        "admin-key-456": ["read", "write", "delete", "admin"],
        "user-key-789": ["read"]
    }
    
    permissions = permissions_map.get(api_key, [])
    
    logger.info(f"User permissions determined: {permissions}")
    return permissions

# 7. CONDITIONAL DEPENDENCIES
def get_rate_limiter(
    request: Request,
    settings: Dict[str, Any] = Depends(get_application_settings)
) -> Dict[str, Any]:
    """
    Dependency for rate limiting.
    
    This dependency demonstrates conditional logic based on
    application settings and request information.
    
    Args:
        request (Request): FastAPI request object
        settings (Dict[str, Any]): Application settings
        
    Returns:
        Dict[str, Any]: Rate limiting information
    """
    client_ip = request.client.host
    
    # Simple rate limiting logic (in production, use Redis or similar)
    if not hasattr(get_rate_limiter, "requests"):
        get_rate_limiter.requests = {}
    
    current_time = time.time()
    client_requests = get_rate_limiter.requests.get(client_ip, [])
    
    # Remove old requests (older than 1 minute)
    client_requests = [req_time for req_time in client_requests if current_time - req_time < 60]
    
    # Add current request
    client_requests.append(current_time)
    get_rate_limiter.requests[client_ip] = client_requests
    
    max_requests = 30  # 30 requests per minute
    
    return {
        "client_ip": client_ip,
        "requests_count": len(client_requests),
        "max_requests": max_requests,
        "remaining": max_requests - len(client_requests),
        "reset_time": current_time + 60
    }

# 8. DEPENDENCY WITH CACHING
class CacheService:
    """
    Service for caching with TTL support.
    
    This demonstrates how to create dependencies that maintain
    their own state and provide caching functionality.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() > self.cache_ttl.get(key, 0):
            del self.cache[key]
            del self.cache_ttl[key]
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL."""
        self.cache[key] = value
        self.cache_ttl[key] = time.time() + ttl
    
    def delete(self, key: str):
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]
            del self.cache_ttl[key]

# Create cache service instance
cache_service = CacheService()

# LINE-BY-LINE EXPLANATION OF DEPENDENCY USAGE:

# 1. BASIC DEPENDENCY USAGE
@app.get("/timestamp")
def get_timestamp(
    current_time: datetime = Depends(get_current_timestamp),
    user_agent: Optional[str] = Depends(get_user_agent),
    request_id: str = Depends(get_request_id)
):
    """
    Endpoint using basic dependencies.
    
    This endpoint demonstrates how to use simple function dependencies.
    Each dependency is automatically called and its result is passed
    to the endpoint function.
    
    Args:
        current_time (datetime): Current timestamp from dependency
        user_agent (Optional[str]): User agent from dependency
        request_id (str): Request ID from dependency
        
    Returns:
        dict: Response with dependency results
    """
    return {
        "message": "Current timestamp with dependencies",
        "timestamp": current_time,
        "user_agent": user_agent,
        "request_id": request_id
    }

# 2. DEPENDENCY WITH PARAMETERS
@app.get("/users")
def list_users(
    pagination: Dict[str, int] = Depends(get_pagination_params),
    user_service: UserService = Depends(UserService)
):
    """
    Endpoint using parameterized dependencies.
    
    This endpoint demonstrates how dependencies can extract
    query parameters and provide them in a structured format.
    
    Args:
        pagination (Dict[str, int]): Pagination parameters
        user_service (UserService): User service instance
        
    Returns:
        dict: Paginated user list
    """
    # Simulate getting users with pagination
    total_users = user_service.get_user_count()
    users = []
    
    for i in range(pagination["skip"], min(pagination["skip"] + pagination["limit"], total_users)):
        user = user_service.get_user_by_id(i + 1)
        if user:
            users.append(user)
    
    return {
        "users": users,
        "pagination": {
            "skip": pagination["skip"],
            "limit": pagination["limit"],
            "total": total_users
        }
    }

# 3. CACHED DEPENDENCY USAGE
@app.get("/settings")
def get_settings(
    settings: Dict[str, Any] = Depends(get_application_settings),
    request_id: str = Depends(get_request_id)
):
    """
    Endpoint using cached dependency.
    
    This endpoint demonstrates how cached dependencies work.
    The get_application_settings function is only called once
    and the result is cached for subsequent requests.
    
    Args:
        settings (Dict[str, Any]): Application settings (cached)
        request_id (str): Request ID for tracking
        
    Returns:
        dict: Application settings
    """
    return {
        "message": "Application settings (cached)",
        "settings": settings,
        "request_id": request_id
    }

# 4. DEPENDENCY WITH VALIDATION
@app.get("/protected")
def protected_endpoint(
    api_key: str = Depends(validate_api_key),
    permissions: List[str] = Depends(get_user_permissions),
    timestamp: datetime = Depends(get_current_timestamp)
):
    """
    Protected endpoint requiring API key validation.
    
    This endpoint demonstrates how dependencies can provide
    authentication and authorization functionality.
    
    Args:
        api_key (str): Validated API key
        permissions (List[str]): User permissions
        timestamp (datetime): Request timestamp
        
    Returns:
        dict: Protected data
    """
    return {
        "message": "Access granted to protected resource",
        "api_key": api_key,
        "permissions": permissions,
        "accessed_at": timestamp,
        "data": "This is protected data"
    }

# 5. DEPENDENCY WITH RATE LIMITING
@app.get("/rate-limited")
def rate_limited_endpoint(
    rate_limit: Dict[str, Any] = Depends(get_rate_limiter),
    request_id: str = Depends(get_request_id)
):
    """
    Endpoint with rate limiting dependency.
    
    This endpoint demonstrates how to implement rate limiting
    using dependencies that track request frequency.
    
    Args:
        rate_limit (Dict[str, Any]): Rate limiting information
        request_id (str): Request ID
        
    Returns:
        dict: Response with rate limit information
        
    Raises:
        HTTPException: When rate limit is exceeded
    """
    if rate_limit["remaining"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limit["max_requests"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(rate_limit["reset_time"]))
            }
        )
    
    return {
        "message": "Rate limited endpoint accessed successfully",
        "rate_limit": rate_limit,
        "request_id": request_id
    }

# 6. DEPENDENCY WITH CACHING SERVICE
@app.get("/cached-data/{key}")
def get_cached_data(
    key: str,
    cache: CacheService = Depends(lambda: cache_service)
):
    """
    Endpoint that uses caching service dependency.
    
    This endpoint demonstrates how to use a caching service
    to store and retrieve data efficiently.
    
    Args:
        key (str): Cache key to retrieve
        cache (CacheService): Cache service instance
        
    Returns:
        dict: Cached data or indication that data is not cached
    """
    cached_value = cache.get(key)
    
    if cached_value is None:
        # Generate new data if not cached
        new_data = {
            "key": key,
            "value": f"Generated value for {key}",
            "generated_at": datetime.now().isoformat()
        }
        
        # Cache the new data
        cache.set(key, new_data, ttl=60)  # Cache for 1 minute
        
        return {
            "message": "Data generated and cached",
            "data": new_data,
            "cached": False
        }
    
    return {
        "message": "Data retrieved from cache",
        "data": cached_value,
        "cached": True
    }

# 7. DEPENDENCY WITH COMPLEX LOGIC
def get_user_context(
    api_key: str = Depends(validate_api_key),
    permissions: List[str] = Depends(get_user_permissions),
    user_service: UserService = Depends(UserService),
    settings: Dict[str, Any] = Depends(get_application_settings)
) -> Dict[str, Any]:
    """
    Complex dependency that combines multiple sub-dependencies.
    
    This dependency demonstrates how to combine multiple dependencies
    to create a comprehensive user context.
    
    Args:
        api_key (str): Validated API key
        permissions (List[str]): User permissions
        user_service (UserService): User service instance
        settings (Dict[str, Any]): Application settings
        
    Returns:
        Dict[str, Any]: Complete user context
    """
    # Determine user level based on permissions
    if "admin" in permissions:
        user_level = "admin"
    elif "write" in permissions:
        user_level = "editor"
    else:
        user_level = "viewer"
    
    # Get additional user info
    user_count = user_service.get_user_count()
    
    return {
        "api_key": api_key,
        "permissions": permissions,
        "user_level": user_level,
        "user_count": user_count,
        "app_name": settings["app_name"],
        "debug_mode": settings["debug"],
        "context_created_at": datetime.now()
    }

@app.get("/user-dashboard")
def user_dashboard(
    user_context: Dict[str, Any] = Depends(get_user_context)
):
    """
    Endpoint using complex dependency with user context.
    
    This endpoint demonstrates how a complex dependency can
    provide a complete context for the endpoint.
    
    Args:
        user_context (Dict[str, Any]): Complete user context
        
    Returns:
        dict: User dashboard data
    """
    return {
        "message": "User dashboard data",
        "user_context": user_context,
        "dashboard_data": {
            "widgets": ["stats", "recent_activity", "notifications"],
            "theme": "default",
            "layout": "grid"
        }
    }

# 8. DEPENDENCY OVERRIDE (FOR TESTING)
def get_test_database():
    """Test database dependency for testing purposes."""
    return {
        "connection_id": "test_connection",
        "connected_at": datetime.now(),
        "status": "test_mode"
    }

# Example of how to override dependencies for testing
# app.dependency_overrides[database.get_connection] = get_test_database

# UTILITY ENDPOINTS

@app.post("/cache/{key}")
def set_cache_data(
    key: str,
    value: Dict[str, Any],
    ttl: int = 300,
    cache: CacheService = Depends(lambda: cache_service)
):
    """Set data in cache."""
    cache.set(key, value, ttl)
    return {
        "message": "Data cached successfully",
        "key": key,
        "ttl": ttl
    }

@app.delete("/cache/{key}")
def delete_cache_data(
    key: str,
    cache: CacheService = Depends(lambda: cache_service)
):
    """Delete data from cache."""
    cache.delete(key)
    return {
        "message": "Cache entry deleted",
        "key": key
    }

@app.get("/")
def root():
    """Root endpoint with dependency injection examples."""
    return {
        "message": "FastAPI Dependency Injection Tutorial",
        "examples": {
            "basic_dependencies": "/timestamp",
            "pagination": "/users?skip=0&limit=5",
            "cached_dependency": "/settings",
            "protected_endpoint": "/protected (requires X-API-Key header)",
            "rate_limited": "/rate-limited",
            "cached_data": "/cached-data/example-key",
            "user_dashboard": "/user-dashboard (requires X-API-Key header)",
            "cache_management": "POST/DELETE /cache/{key}"
        },
        "dependency_patterns": {
            "function_dependencies": "Simple functions that return values",
            "class_dependencies": "Classes that provide services",
            "cached_dependencies": "Dependencies with caching using @lru_cache",
            "parameterized_dependencies": "Dependencies that accept parameters",
            "sub_dependencies": "Dependencies that depend on other dependencies",
            "validation_dependencies": "Dependencies that validate and authenticate",
            "service_dependencies": "Business logic encapsulated in services",
            "conditional_dependencies": "Dependencies with conditional logic"
        },
        "api_key_examples": {
            "admin": "admin-key-456",
            "user": "user-key-789",
            "secret": "secret-key-123"
        }
    }

# WHAT YOU'VE LEARNED:
"""
1. Dependency Injection Basics:
   - Functions as dependencies with Depends()
   - Automatic dependency resolution and injection
   - Dependency parameters and validation
   - Reusable components across endpoints

2. Dependency Types:
   - Simple function dependencies
   - Class-based dependencies with state
   - Cached dependencies with @lru_cache
   - Parameterized dependencies with validation
   - Sub-dependencies that depend on other dependencies

3. Common Dependency Patterns:
   - Authentication and authorization
   - Database connections and services
   - Request validation and processing
   - Rate limiting and throttling
   - Caching and data management
   - Configuration and settings

4. Advanced Features:
   - Dependency caching and scoping
   - Conditional dependency logic
   - Service layer architecture
   - Dependency override for testing
   - Complex dependency hierarchies

5. Best Practices:
   - Keep dependencies focused and single-purpose
   - Use type hints for better IDE support
   - Cache expensive dependencies appropriately
   - Structure dependencies in a hierarchy
   - Use dependency injection for testability

6. Real-world Applications:
   - User authentication systems
   - Database connection management
   - API rate limiting
   - Request validation and processing
   - Service layer architecture
   - Configuration management

NEXT: Move to 09_authentication.py to learn about security and authentication!
""" 