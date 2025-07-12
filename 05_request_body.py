"""
📤 FastAPI Request Body - POST Data and Pydantic Models

This file teaches you everything about request bodies in FastAPI:
- Pydantic models for data validation
- POST, PUT, PATCH request bodies
- Nested models and complex data structures
- Form data and file uploads
- Custom validation and serialization

Run this file with: uvicorn 05_request_body:app --reload
"""

from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Union
from datetime import datetime, date
from enum import Enum
import json

# Create FastAPI application
app = FastAPI(
    title="FastAPI Request Body Tutorial",
    description="Master request bodies and Pydantic models",
    version="1.0.0"
)

# ENUMS FOR VALIDATION
class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    guest = "guest"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

# In-memory storage for examples
users_db = {}
posts_db = {}
next_user_id = 1
next_post_id = 1

# LINE-BY-LINE EXPLANATION OF PYDANTIC MODELS:

# 1. BASIC PYDANTIC MODEL
class User(BaseModel):
    """
    Basic Pydantic model for user data validation.
    
    Pydantic models define the structure and validation rules for request bodies.
    Each field has a type annotation that enables automatic validation.
    """
    # Required fields (no default value)
    name: str                           # Required string field
    email: EmailStr                     # Email validation (requires email-validator)
    age: int                           # Required integer field
    
    # Optional fields (with default values)
    is_active: bool = True             # Boolean with default True
    role: UserRole = UserRole.user     # Enum with default value
    bio: Optional[str] = None          # Optional string field
    
    # Field with validation constraints
    password: str = Field(
        ...,                           # Required field (same as no default)
        min_length=8,                  # Minimum length validation
        max_length=50,                 # Maximum length validation
        description="User password"    # Field description for docs
    )
    
    # Custom validation using validators
    @validator('age')
    def validate_age(cls, v):
        """
        Custom validator for age field.
        
        Validators run after type conversion but before the model is created.
        They can transform values or raise ValueError for validation errors.
        """
        if v < 0:
            raise ValueError('Age must be positive')
        if v > 150:
            raise ValueError('Age must be realistic')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Custom validator for name field."""
        if len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v.strip().title()  # Clean and format the name

# 2. MODEL WITH NESTED OBJECTS
class Address(BaseModel):
    """Nested model for address information."""
    street: str
    city: str
    state: str
    zip_code: str = Field(..., regex=r'^\d{5}(-\d{4})?$')  # US ZIP code format
    country: str = "USA"

class UserWithAddress(BaseModel):
    """User model with nested address information."""
    name: str
    email: EmailStr
    age: int
    address: Address                    # Nested Pydantic model
    emergency_contacts: List[str] = []  # List of strings
    
    class Config:
        """
        Pydantic configuration class.
        
        The Config class allows you to customize model behavior:
        - schema_extra: Add examples to the generated schema
        - validate_assignment: Validate when fields are assigned after creation
        - allow_population_by_field_name: Allow using field names for population
        """
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "USA"
                },
                "emergency_contacts": ["jane@example.com", "bob@example.com"]
            }
        }

# 3. COMPLEX MODEL WITH MULTIPLE TYPES
class PostContent(BaseModel):
    """Model for different types of post content."""
    content_type: str = Field(..., regex="^(text|image|video|link)$")
    data: Union[str, Dict] = Field(..., description="Content data - varies by type")
    
    @validator('data')
    def validate_content_data(cls, v, values):
        """Validate data based on content type."""
        content_type = values.get('content_type')
        
        if content_type == 'text' and not isinstance(v, str):
            raise ValueError('Text content must be a string')
        elif content_type == 'link' and isinstance(v, dict):
            required_keys = {'url', 'title'}
            if not required_keys.issubset(v.keys()):
                raise ValueError('Link content must have url and title')
        
        return v

class Post(BaseModel):
    """Complete post model with content and metadata."""
    title: str = Field(..., min_length=1, max_length=200)
    content: PostContent
    author_id: int
    tags: List[str] = []
    priority: Priority = Priority.medium
    is_published: bool = False
    scheduled_at: Optional[datetime] = None
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        """Ensure scheduled time is in the future."""
        if v and v <= datetime.now():
            raise ValueError('Scheduled time must be in the future')
        return v

# 4. UPDATE MODELS (PARTIAL UPDATES)
class UserUpdate(BaseModel):
    """Model for partial user updates (all fields optional)."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    bio: Optional[str] = None
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v

# LINE-BY-LINE EXPLANATION OF REQUEST BODY ENDPOINTS:

# 1. BASIC POST REQUEST WITH REQUEST BODY
@app.post("/users", response_model=User)
def create_user(user: User):
    """
    Create a new user with request body validation.
    
    The 'user' parameter automatically receives and validates the JSON request body.
    FastAPI uses the User model to validate incoming data.
    
    Args:
        user (User): User data from request body (automatically validated)
        
    Returns:
        User: The created user with assigned ID
        
    Request Body Example:
        {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "password": "securepassword123",
            "role": "user"
        }
    """
    global next_user_id
    
    # Convert Pydantic model to dictionary
    user_dict = user.dict()
    user_dict["id"] = next_user_id
    user_dict["created_at"] = datetime.now().isoformat()
    
    # Store in our "database"
    users_db[next_user_id] = user_dict
    next_user_id += 1
    
    # Remove password from response (security best practice)
    response_dict = user_dict.copy()
    del response_dict["password"]
    
    return response_dict

# 2. POST WITH NESTED MODEL
@app.post("/users-with-address")
def create_user_with_address(user: UserWithAddress):
    """
    Create user with nested address information.
    
    This demonstrates how FastAPI handles nested Pydantic models.
    The entire nested structure is validated automatically.
    
    Args:
        user (UserWithAddress): User data with nested address
        
    Returns:
        dict: Created user information
        
    Request Body Example:
        {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "age": 28,
            "address": {
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90210"
            },
            "emergency_contacts": ["bob@example.com"]
        }
    """
    global next_user_id
    
    user_dict = user.dict()
    user_dict["id"] = next_user_id
    user_dict["created_at"] = datetime.now().isoformat()
    
    users_db[next_user_id] = user_dict
    next_user_id += 1
    
    return {
        "message": "User with address created successfully",
        "user": user_dict
    }

# 3. PUT REQUEST FOR COMPLETE REPLACEMENT
@app.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    """
    Replace entire user record (PUT method).
    
    PUT is used for complete resource replacement.
    All required fields must be provided.
    
    Args:
        user_id (int): ID of user to update
        user (User): Complete new user data
        
    Returns:
        dict: Updated user information
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Replace entire user record
    user_dict = user.dict()
    user_dict["id"] = user_id
    user_dict["updated_at"] = datetime.now().isoformat()
    
    # Keep original creation time if it exists
    if "created_at" in users_db[user_id]:
        user_dict["created_at"] = users_db[user_id]["created_at"]
    
    users_db[user_id] = user_dict
    
    # Remove password from response
    response_dict = user_dict.copy()
    del response_dict["password"]
    
    return {"message": "User updated successfully", "user": response_dict}

# 4. PATCH REQUEST FOR PARTIAL UPDATES
@app.patch("/users/{user_id}")
def patch_user(user_id: int, user_update: UserUpdate):
    """
    Partially update user record (PATCH method).
    
    PATCH is used for partial updates where only specified fields are changed.
    Only provided fields will be updated.
    
    Args:
        user_id (int): ID of user to update
        user_update (UserUpdate): Partial user data (only fields to update)
        
    Returns:
        dict: Updated user information
        
    Request Body Example (only update name and age):
        {
            "name": "John Smith",
            "age": 31
        }
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get existing user
    existing_user = users_db[user_id].copy()
    
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)  # Only include set fields
    for field, value in update_data.items():
        existing_user[field] = value
    
    existing_user["updated_at"] = datetime.now().isoformat()
    users_db[user_id] = existing_user
    
    # Remove password from response
    response_dict = existing_user.copy()
    if "password" in response_dict:
        del response_dict["password"]
    
    return {"message": "User updated successfully", "user": response_dict}

# 5. COMPLEX REQUEST BODY WITH VALIDATION
@app.post("/posts")
def create_post(post: Post):
    """
    Create a post with complex validation.
    
    This endpoint demonstrates complex model validation including:
    - Union types for flexible content
    - Custom validators
    - Conditional validation
    - DateTime handling
    
    Args:
        post (Post): Post data with complex validation
        
    Returns:
        dict: Created post information
        
    Request Body Examples:
        Text Post:
        {
            "title": "My First Post",
            "content": {
                "content_type": "text",
                "data": "This is a text post content."
            },
            "author_id": 1,
            "tags": ["blog", "intro"],
            "priority": "medium"
        }
        
        Link Post:
        {
            "title": "Interesting Article",
            "content": {
                "content_type": "link",
                "data": {
                    "url": "https://example.com",
                    "title": "Example Article"
                }
            },
            "author_id": 1,
            "priority": "high"
        }
    """
    global next_post_id
    
    # Validate that author exists
    if post.author_id not in users_db:
        raise HTTPException(status_code=400, detail="Author not found")
    
    post_dict = post.dict()
    post_dict["id"] = next_post_id
    post_dict["created_at"] = datetime.now().isoformat()
    
    posts_db[next_post_id] = post_dict
    next_post_id += 1
    
    return {"message": "Post created successfully", "post": post_dict}

# 6. MULTIPLE REQUEST BODY PARAMETERS
@app.post("/posts-with-metadata")
def create_post_with_metadata(
    post: Post,
    metadata: Dict[str, Union[str, int, bool]] = {},
    notify_followers: bool = True
):
    """
    Multiple request body parameters.
    
    You can have multiple body parameters in a single endpoint.
    FastAPI will combine them into a single JSON object.
    
    Args:
        post (Post): Post data
        metadata (Dict): Additional metadata
        notify_followers (bool): Whether to notify followers
        
    Expected Request Body:
        {
            "post": {
                "title": "My Post",
                "content": {...},
                "author_id": 1
            },
            "metadata": {
                "source": "mobile_app",
                "version": "1.2.3"
            },
            "notify_followers": true
        }
    """
    global next_post_id
    
    post_dict = post.dict()
    post_dict["id"] = next_post_id
    post_dict["metadata"] = metadata
    post_dict["created_at"] = datetime.now().isoformat()
    
    posts_db[next_post_id] = post_dict
    next_post_id += 1
    
    # Simulate notification logic
    notification_sent = notify_followers and post.is_published
    
    return {
        "message": "Post created with metadata",
        "post": post_dict,
        "notification_sent": notification_sent
    }

# 7. FORM DATA HANDLING
@app.post("/upload-profile")
def upload_user_profile(
    name: str = Form(...),
    email: str = Form(...),
    age: int = Form(...),
    bio: str = Form(""),
    profile_picture: UploadFile = File(...)
):
    """
    Handle form data including file uploads.
    
    Form data is used for HTML forms and file uploads.
    Each field is specified with Form() and files with File().
    
    Args:
        name (str): User name from form field
        email (str): User email from form field
        age (int): User age from form field
        bio (str): User bio from form field (optional)
        profile_picture (UploadFile): Uploaded profile picture
        
    Returns:
        dict: Upload confirmation with file info
        
    Note: This endpoint expects multipart/form-data content type,
    not application/json. Test with HTML form or tools like curl.
    """
    # File validation
    allowed_types = ["image/jpeg", "image/png", "image/gif"]
    if profile_picture.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPEG, PNG, and GIF are allowed."
        )
    
    # File size validation (2MB limit)
    max_size = 2 * 1024 * 1024  # 2MB in bytes
    if profile_picture.size and profile_picture.size > max_size:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 2MB."
        )
    
    return {
        "message": "Profile uploaded successfully",
        "user_data": {
            "name": name,
            "email": email,
            "age": age,
            "bio": bio
        },
        "file_info": {
            "filename": profile_picture.filename,
            "content_type": profile_picture.content_type,
            "size": profile_picture.size
        }
    }

# 8. MIXED PATH, QUERY, AND BODY PARAMETERS
@app.put("/users/{user_id}/posts/{post_id}")
def update_user_post(
    user_id: int,                      # Path parameter
    post_id: int,                      # Path parameter
    post: Post,                        # Request body
    notify: bool = False,              # Query parameter
    reason: Optional[str] = None       # Query parameter
):
    """
    Endpoint combining path parameters, query parameters, and request body.
    
    This demonstrates how FastAPI handles different parameter types:
    - Path parameters: From URL path
    - Query parameters: From URL query string
    - Request body: From JSON body
    
    Args:
        user_id (int): User ID from path
        post_id (int): Post ID from path
        post (Post): Updated post data from body
        notify (bool): Whether to send notifications (query)
        reason (str): Update reason (query, optional)
        
    URL Example: PUT /users/1/posts/5?notify=true&reason=correction
    """
    # Validate user exists
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate post exists
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Validate user owns the post
    if posts_db[post_id]["author_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    
    # Update the post
    post_dict = post.dict()
    post_dict["id"] = post_id
    post_dict["updated_at"] = datetime.now().isoformat()
    if reason:
        post_dict["update_reason"] = reason
    
    posts_db[post_id] = post_dict
    
    return {
        "message": "Post updated successfully",
        "post": post_dict,
        "notifications_sent": notify,
        "update_reason": reason
    }

# UTILITY ENDPOINTS FOR TESTING

@app.get("/users")
def list_users():
    """List all users for testing purposes."""
    users_without_passwords = []
    for user in users_db.values():
        user_copy = user.copy()
        if "password" in user_copy:
            del user_copy["password"]
        users_without_passwords.append(user_copy)
    return {"users": users_without_passwords}

@app.get("/posts")
def list_posts():
    """List all posts for testing purposes."""
    return {"posts": list(posts_db.values())}

@app.get("/")
def root():
    """Root endpoint with examples and documentation."""
    return {
        "message": "FastAPI Request Body Tutorial",
        "endpoints": {
            "create_user": "POST /users",
            "create_user_with_address": "POST /users-with-address",
            "update_user": "PUT /users/{user_id}",
            "patch_user": "PATCH /users/{user_id}",
            "create_post": "POST /posts",
            "create_post_with_metadata": "POST /posts-with-metadata",
            "upload_profile": "POST /upload-profile (form data)",
            "update_user_post": "PUT /users/{user_id}/posts/{post_id}"
        },
        "model_features": {
            "validation": "Automatic type and constraint validation",
            "nested_models": "Support for complex nested structures",
            "custom_validators": "Custom validation logic with @validator",
            "field_constraints": "Field-level validation with Field()",
            "partial_updates": "Models for PATCH operations",
            "form_data": "Handle HTML forms and file uploads",
            "multiple_bodies": "Multiple request body parameters"
        },
        "tips": [
            "Use Pydantic models for automatic validation",
            "Implement custom validators for business logic",
            "Use separate models for create/update operations",
            "Handle file uploads with UploadFile",
            "Combine path, query, and body parameters as needed"
        ]
    }

# WHAT YOU'VE LEARNED:
"""
1. Pydantic Models:
   - Define data structure and validation rules
   - Automatic type conversion and validation
   - Custom validators with @validator decorator
   - Field constraints with Field()
   - Nested models for complex data

2. Request Body Types:
   - JSON data with Pydantic models
   - Form data with Form() parameters
   - File uploads with UploadFile
   - Multiple body parameters in one endpoint

3. HTTP Methods and Bodies:
   - POST: Create new resources
   - PUT: Replace entire resources
   - PATCH: Partial updates
   - All can include request bodies

4. Validation Features:
   - Type validation (automatic)
   - Range validation (min/max values)
   - String validation (length, regex)
   - Email validation with EmailStr
   - Custom business logic validation

5. Best Practices:
   - Use different models for create/update
   - Validate file types and sizes
   - Remove sensitive data from responses
   - Provide clear error messages
   - Use appropriate HTTP methods

NEXT: Move to intermediate level with 06_response_models.py!
""" 