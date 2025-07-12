"""
📤 FastAPI Response Models - Controlling API Responses

This file teaches you everything about response models in FastAPI:
- Response model validation and serialization
- Different response types and status codes
- Custom response classes
- Response headers and cookies
- Excluding fields from responses

Run this file with: uvicorn 06_response_models:app --reload
"""

from fastapi import FastAPI, HTTPException, status, Response, Cookie, Header
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import json

# Create FastAPI application
app = FastAPI(
    title="FastAPI Response Models Tutorial",
    description="Master response models, status codes, and response handling",
    version="1.0.0"
)

# ENUMS FOR RESPONSE EXAMPLES
class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"

class ResponseFormat(str, Enum):
    json = "json"
    xml = "xml"
    text = "text"

# LINE-BY-LINE EXPLANATION OF RESPONSE MODELS:

# 1. BASIC RESPONSE MODEL
class UserResponse(BaseModel):
    """
    Response model for user data.
    
    Response models define the structure of API responses.
    They automatically validate outgoing data and generate documentation.
    """
    id: int
    name: str
    email: str
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        """
        Configuration for the response model.
        
        - schema_extra: Provides example data for documentation
        - orm_mode: Allows the model to read data from ORM objects
        """
        schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active",
                "created_at": "2023-01-01T12:00:00",
                "last_login": "2023-12-01T10:30:00"
            }
        }

# 2. RESPONSE MODEL WITH EXCLUDED FIELDS
class UserCreateRequest(BaseModel):
    """Request model for creating users (includes password)."""
    name: str
    email: str
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None

class UserCreateResponse(BaseModel):
    """Response model for user creation (excludes password)."""
    id: int
    name: str
    email: str
    status: UserStatus
    created_at: datetime
    message: str = "User created successfully"

# 3. NESTED RESPONSE MODELS
class AddressResponse(BaseModel):
    """Response model for address data."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str

class UserDetailResponse(BaseModel):
    """Detailed user response with nested address."""
    id: int
    name: str
    email: str
    status: UserStatus
    address: Optional[AddressResponse] = None
    preferences: Dict[str, Any] = {}
    tags: List[str] = []

# 4. PAGINATED RESPONSE MODEL
class PaginationInfo(BaseModel):
    """Model for pagination metadata."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class PaginatedUsersResponse(BaseModel):
    """Paginated response model for user lists."""
    users: List[UserResponse]
    pagination: PaginationInfo

# 5. API RESPONSE WRAPPER
class ApiResponse(BaseModel):
    """
    Generic API response wrapper.
    
    This pattern is common in APIs to provide consistent response structure
    with success indicators, messages, and data.
    """
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Mock database for examples
users_db = {
    1: {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "password": "hashedpassword123",
        "phone": "+1234567890",
        "status": UserStatus.active,
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "last_login": datetime(2023, 12, 1, 10, 30, 0),
        "address": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA"
        },
        "preferences": {"theme": "dark", "notifications": True},
        "tags": ["admin", "power-user"]
    },
    2: {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "password": "hashedpassword456",
        "status": UserStatus.inactive,
        "created_at": datetime(2023, 2, 15, 14, 30, 0),
        "last_login": None,
        "preferences": {"theme": "light"},
        "tags": ["user"]
    }
}

# LINE-BY-LINE EXPLANATION OF RESPONSE ENDPOINTS:

# 1. BASIC RESPONSE MODEL USAGE
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """
    Get user by ID with response model validation.
    
    The response_model parameter tells FastAPI:
    - What the response should look like
    - How to validate the response data
    - What to include in the API documentation
    - How to serialize the response
    
    Args:
        user_id (int): User ID to retrieve
        
    Returns:
        UserResponse: User data (automatically validated)
        
    The response_model ensures that:
    - Only defined fields are returned
    - Data types are correct
    - Documentation is generated
    - Sensitive fields (like password) are excluded
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    
    # FastAPI automatically validates this against UserResponse model
    # and excludes any fields not defined in the model
    return user

# 2. RESPONSE WITH CUSTOM STATUS CODE
@app.post("/users", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreateRequest):
    """
    Create user with custom status code.
    
    The status_code parameter sets the HTTP status code for successful responses.
    201 Created is appropriate for resource creation endpoints.
    
    Args:
        user (UserCreateRequest): User creation data
        
    Returns:
        UserCreateResponse: Created user data (excludes password)
        
    Notice how the response model automatically excludes the password field
    even though it was provided in the request.
    """
    # Generate new user ID
    new_id = max(users_db.keys()) + 1 if users_db else 1
    
    # Create user record
    user_data = user.dict()
    user_data.update({
        "id": new_id,
        "status": UserStatus.active,
        "created_at": datetime.now()
    })
    
    users_db[new_id] = user_data
    
    # Return response (password automatically excluded by response model)
    return user_data

# 3. RESPONSE MODEL WITH NESTED DATA
@app.get("/users/{user_id}/details", response_model=UserDetailResponse)
def get_user_details(user_id: int):
    """
    Get detailed user information with nested response model.
    
    This demonstrates how response models handle nested data structures.
    The AddressResponse model is automatically applied to the address field.
    
    Args:
        user_id (int): User ID to retrieve details for
        
    Returns:
        UserDetailResponse: Detailed user data with nested address
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    # FastAPI automatically handles nested model validation
    return user

# 4. PAGINATED RESPONSE
@app.get("/users", response_model=PaginatedUsersResponse)
def list_users(page: int = 1, page_size: int = 10):
    """
    List users with paginated response model.
    
    This demonstrates how to structure paginated API responses
    with both data and pagination metadata.
    
    Args:
        page (int): Page number (1-based)
        page_size (int): Number of items per page
        
    Returns:
        PaginatedUsersResponse: Paginated user list with metadata
    """
    # Calculate pagination
    total_items = len(users_db)
    total_pages = (total_items + page_size - 1) // page_size
    offset = (page - 1) * page_size
    
    # Get users for current page
    users_list = list(users_db.values())
    page_users = users_list[offset:offset + page_size]
    
    # Build pagination info
    pagination = PaginationInfo(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    
    return {
        "users": page_users,
        "pagination": pagination
    }

# 5. MULTIPLE RESPONSE MODELS FOR DIFFERENT STATUS CODES
@app.get(
    "/users/{user_id}/status",
    responses={
        200: {"model": UserResponse, "description": "User found"},
        404: {"model": ApiResponse, "description": "User not found"},
        403: {"model": ApiResponse, "description": "Access denied"}
    }
)
def get_user_status(user_id: int, admin_access: bool = False):
    """
    Endpoint with multiple possible response models.
    
    The responses parameter allows you to document different response models
    for different HTTP status codes. This is useful for comprehensive API documentation.
    
    Args:
        user_id (int): User ID to check status for
        admin_access (bool): Whether request has admin privileges
        
    Returns:
        Union[UserResponse, ApiResponse]: Different response based on conditions
    """
    if user_id not in users_db:
        # Return structured error response
        return JSONResponse(
            status_code=404,
            content=ApiResponse(
                success=False,
                message="User not found",
                errors=["User with specified ID does not exist"]
            ).dict()
        )
    
    user = users_db[user_id]
    
    # Check access permissions
    if user["status"] == UserStatus.suspended and not admin_access:
        return JSONResponse(
            status_code=403,
            content=ApiResponse(
                success=False,
                message="Access denied",
                errors=["User account is suspended"]
            ).dict()
        )
    
    # Return successful response
    return user

# 6. RESPONSE WITH EXCLUDED FIELDS
@app.get("/users/{user_id}/public", response_model=UserResponse, response_model_exclude={"last_login"})
def get_user_public(user_id: int):
    """
    Get user data with specific fields excluded from response.
    
    The response_model_exclude parameter allows you to exclude specific fields
    from the response model at the endpoint level.
    
    Args:
        user_id (int): User ID to retrieve
        
    Returns:
        UserResponse: User data without last_login field
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return users_db[user_id]

# 7. RESPONSE WITH ONLY SPECIFIC FIELDS
@app.get("/users/{user_id}/summary", response_model=UserResponse, response_model_include={"id", "name", "email", "status"})
def get_user_summary(user_id: int):
    """
    Get user summary with only specific fields included.
    
    The response_model_include parameter allows you to include only specific fields
    in the response, even if the model has more fields.
    
    Args:
        user_id (int): User ID to retrieve summary for
        
    Returns:
        UserResponse: User data with only specified fields
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return users_db[user_id]

# 8. CUSTOM RESPONSE CLASS
@app.get("/users/{user_id}/export")
def export_user_data(user_id: int, format: ResponseFormat = ResponseFormat.json):
    """
    Export user data in different formats using custom response classes.
    
    This demonstrates how to return different response types based on parameters.
    FastAPI provides various response classes for different content types.
    
    Args:
        user_id (int): User ID to export
        format (ResponseFormat): Export format (json, xml, text)
        
    Returns:
        Response: Different response type based on format parameter
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    if format == ResponseFormat.json:
        # Return JSON response (default)
        return JSONResponse(content=user)
    
    elif format == ResponseFormat.xml:
        # Return XML response
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<user>
    <id>{user['id']}</id>
    <name>{user['name']}</name>
    <email>{user['email']}</email>
    <status>{user['status']}</status>
</user>"""
        return Response(content=xml_content, media_type="application/xml")
    
    elif format == ResponseFormat.text:
        # Return plain text response
        text_content = f"""User Information
ID: {user['id']}
Name: {user['name']}
Email: {user['email']}
Status: {user['status']}
Created: {user['created_at']}"""
        return PlainTextResponse(content=text_content)

# 9. RESPONSE WITH HEADERS AND COOKIES
@app.get("/users/{user_id}/profile")
def get_user_profile(user_id: int):
    """
    Get user profile with custom headers and cookies.
    
    This demonstrates how to add custom headers and cookies to responses.
    Useful for caching, tracking, or providing additional metadata.
    
    Args:
        user_id (int): User ID to retrieve profile for
        
    Returns:
        JSONResponse: User profile with custom headers and cookies
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    # Create response with custom headers
    response = JSONResponse(content=user)
    
    # Add custom headers
    response.headers["X-User-ID"] = str(user_id)
    response.headers["X-Request-Time"] = datetime.now().isoformat()
    response.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
    
    # Set cookies
    response.set_cookie(
        key="last_viewed_user",
        value=str(user_id),
        max_age=3600,  # 1 hour
        httponly=True,  # Prevent JavaScript access
        secure=True,    # Only send over HTTPS
        samesite="strict"  # CSRF protection
    )
    
    return response

# 10. STREAMING RESPONSE
@app.get("/users/export/csv")
def export_users_csv():
    """
    Export users as CSV with streaming response.
    
    This demonstrates how to create streaming responses for large datasets.
    Useful for file downloads or large data exports.
    
    Returns:
        Response: CSV file stream
    """
    def generate_csv():
        """Generator function to create CSV data."""
        # CSV header
        yield "id,name,email,status,created_at\n"
        
        # CSV rows
        for user in users_db.values():
            yield f"{user['id']},{user['name']},{user['email']},{user['status']},{user['created_at']}\n"
    
    return Response(
        content=generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )

# 11. CONDITIONAL RESPONSE MODELS
@app.get("/users/{user_id}/data")
def get_user_data(user_id: int, include_sensitive: bool = False):
    """
    Return different response models based on conditions.
    
    This demonstrates how to conditionally return different response structures
    based on request parameters or user permissions.
    
    Args:
        user_id (int): User ID to retrieve
        include_sensitive (bool): Whether to include sensitive data
        
    Returns:
        Union[UserResponse, UserDetailResponse]: Different response based on permissions
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    if include_sensitive:
        # Return detailed response with all data
        return JSONResponse(
            content=user,
            headers={"X-Response-Type": "detailed"}
        )
    else:
        # Return basic response without sensitive data
        basic_user = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "status": user["status"],
            "created_at": user["created_at"],
            "last_login": user.get("last_login")
        }
        return JSONResponse(
            content=basic_user,
            headers={"X-Response-Type": "basic"}
        )

# UTILITY ENDPOINTS

@app.get("/")
def root():
    """Root endpoint with examples and documentation."""
    return {
        "message": "FastAPI Response Models Tutorial",
        "examples": {
            "basic_response": "/users/1",
            "create_user": "POST /users",
            "user_details": "/users/1/details",
            "paginated_users": "/users?page=1&page_size=5",
            "user_status": "/users/1/status",
            "public_profile": "/users/1/public",
            "user_summary": "/users/1/summary",
            "export_formats": "/users/1/export?format=json",
            "user_profile": "/users/1/profile",
            "csv_export": "/users/export/csv",
            "conditional_data": "/users/1/data?include_sensitive=true"
        },
        "response_model_features": {
            "validation": "Automatic response validation",
            "serialization": "Convert Python objects to JSON",
            "documentation": "Generate API documentation",
            "type_safety": "Ensure response structure consistency",
            "field_filtering": "Include/exclude specific fields",
            "nested_models": "Handle complex data structures",
            "custom_responses": "Different response types and formats"
        }
    }

# WHAT YOU'VE LEARNED:
"""
1. Response Model Basics:
   - Define response structure with Pydantic models
   - Automatic validation and serialization
   - Generated API documentation
   - Type safety for responses

2. Response Model Features:
   - response_model: Define expected response structure
   - response_model_include: Include only specific fields
   - response_model_exclude: Exclude specific fields
   - status_code: Set HTTP status codes

3. Advanced Response Types:
   - JSONResponse: JSON responses with custom headers
   - PlainTextResponse: Plain text responses
   - Response: Generic response with custom content type
   - FileResponse: File downloads
   - Streaming responses: For large datasets

4. Response Customization:
   - Custom headers and cookies
   - Multiple response models for different status codes
   - Conditional responses based on parameters
   - Different formats (JSON, XML, CSV, etc.)

5. Best Practices:
   - Use response models for consistency
   - Exclude sensitive data from responses
   - Provide meaningful status codes
   - Document different response scenarios
   - Use appropriate response types for content

6. Common Patterns:
   - Paginated responses for lists
   - API response wrappers for consistency
   - Nested models for complex data
   - Conditional field inclusion/exclusion
   - File exports and streaming

NEXT: Move to 07_error_handling.py to learn about exception handling!
""" 