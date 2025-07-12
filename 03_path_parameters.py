"""
🛤️ FastAPI Path Parameters - URL Variables and Validation

This file teaches you everything about path parameters in FastAPI:
- How to define path parameters
- Type conversion and validation
- Path parameter constraints
- Multiple path parameters
- Path parameter with Enum

Run this file with: uvicorn 03_path_parameters:app --reload
"""

from fastapi import FastAPI, HTTPException, Path
from enum import Enum
from typing import Optional
from datetime import datetime

# Create FastAPI application
app = FastAPI(
    title="FastAPI Path Parameters Tutorial",
    description="Master path parameters with validation and constraints",
    version="1.0.0"
)

# ENUM FOR DEMONSTRATING RESTRICTED VALUES
class ModelName(str, Enum):
    """
    Enum class for restricting model names to specific values.
    
    This demonstrates how to limit path parameters to predefined choices.
    FastAPI will automatically validate and provide documentation.
    """
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

# Mock database for examples
users_db = {
    1: {"name": "Alice", "email": "alice@example.com", "age": 30},
    2: {"name": "Bob", "email": "bob@example.com", "age": 25},
    3: {"name": "Charlie", "email": "charlie@example.com", "age": 35}
}

files_db = {
    "document.pdf": {"size": 1024, "type": "pdf"},
    "image.jpg": {"size": 2048, "type": "image"},
    "data.csv": {"size": 512, "type": "csv"}
}

# LINE-BY-LINE EXPLANATION OF PATH PARAMETERS:

# 1. BASIC PATH PARAMETER
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Basic path parameter example.
    
    The {user_id} in the URL path becomes a function parameter.
    FastAPI automatically converts the string from URL to int type.
    
    Args:
        user_id (int): User ID from URL path
        
    Returns:
        dict: User information or error message
        
    Examples:
        GET /users/1 -> Returns user with ID 1
        GET /users/abc -> Returns 422 validation error (not an integer)
    """
    # Type conversion happens automatically
    # If user_id can't be converted to int, FastAPI returns 422 error
    
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user_id,
        "user": users_db[user_id],
        "type_info": f"user_id is of type {type(user_id).__name__}"
    }

# 2. PATH PARAMETER WITH VALIDATION
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(
    user_id: int = Path(..., gt=0, description="The ID of the user"),
    post_id: int = Path(..., gt=0, le=1000, description="The ID of the post")
):
    """
    Multiple path parameters with validation constraints.
    
    The Path() function allows you to add validation and metadata:
    - gt=0: Greater than 0
    - le=1000: Less than or equal to 1000
    - description: Documentation text
    
    Args:
        user_id (int): User ID (must be > 0)
        post_id (int): Post ID (must be > 0 and <= 1000)
        
    Returns:
        dict: Post information
        
    Examples:
        GET /users/1/posts/5 -> Valid request
        GET /users/0/posts/5 -> Error: user_id must be > 0
        GET /users/1/posts/1001 -> Error: post_id must be <= 1000
    """
    # Validation happens before this function is called
    # If validation fails, FastAPI returns 422 error automatically
    
    return {
        "user_id": user_id,
        "post_id": post_id,
        "post": f"Post {post_id} by user {user_id}",
        "validation_passed": True
    }

# 3. STRING PATH PARAMETER WITH CONSTRAINTS
@app.get("/files/{file_path:path}")
def get_file(file_path: str):
    """
    Path parameter that can contain slashes.
    
    The :path converter allows the parameter to match multiple URL segments,
    including forward slashes. Useful for file paths.
    
    Args:
        file_path (str): File path that can contain slashes
        
    Returns:
        dict: File information
        
    Examples:
        GET /files/docs/readme.txt -> file_path = "docs/readme.txt"
        GET /files/images/2023/photo.jpg -> file_path = "images/2023/photo.jpg"
    """
    return {
        "file_path": file_path,
        "segments": file_path.split("/"),
        "filename": file_path.split("/")[-1] if "/" in file_path else file_path,
        "extension": file_path.split(".")[-1] if "." in file_path else None
    }

# 4. ENUM PATH PARAMETER
@app.get("/models/{model_name}")
def get_model(model_name: ModelName):
    """
    Path parameter restricted to enum values.
    
    Using an Enum restricts the parameter to predefined values.
    FastAPI automatically validates and provides documentation with all options.
    
    Args:
        model_name (ModelName): Must be one of: alexnet, resnet, lenet
        
    Returns:
        dict: Model information
        
    Examples:
        GET /models/alexnet -> Valid (returns alexnet info)
        GET /models/resnet -> Valid (returns resnet info)
        GET /models/vgg -> Error: value not in enum
    """
    models_info = {
        ModelName.alexnet: {"description": "AlexNet CNN model", "params": "60M"},
        ModelName.resnet: {"description": "ResNet deep residual model", "params": "25M"},
        ModelName.lenet: {"description": "LeNet classic CNN", "params": "60K"}
    }
    
    return {
        "model_name": model_name,
        "model_info": models_info[model_name],
        "available_models": [model.value for model in ModelName]
    }

# 5. MIXED PATH AND QUERY PARAMETERS
@app.get("/users/{user_id}/profile")
def get_user_profile(
    user_id: int = Path(..., gt=0, description="User ID"),
    include_posts: bool = False,
    include_comments: bool = False
):
    """
    Combining path parameters with query parameters.
    
    Path parameters are required and part of the URL structure.
    Query parameters are optional and come after the ? in the URL.
    
    Args:
        user_id (int): User ID from path (required)
        include_posts (bool): Whether to include posts (query parameter)
        include_comments (bool): Whether to include comments (query parameter)
        
    Returns:
        dict: User profile with optional additional data
        
    Examples:
        GET /users/1/profile -> Basic profile
        GET /users/1/profile?include_posts=true -> Profile with posts
        GET /users/1/profile?include_posts=true&include_comments=true -> Full profile
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = {
        "user_id": user_id,
        "profile": users_db[user_id].copy()
    }
    
    # Add optional data based on query parameters
    if include_posts:
        profile["posts"] = [f"Post {i} by user {user_id}" for i in range(1, 4)]
    
    if include_comments:
        profile["comments"] = [f"Comment {i} by user {user_id}" for i in range(1, 6)]
    
    return profile

# 6. ADVANCED PATH PARAMETER VALIDATION
@app.get("/orders/{order_id}/items/{item_id}")
def get_order_item(
    order_id: str = Path(
        ...,
        min_length=8,
        max_length=12,
        regex="^ORD[0-9]+$",
        description="Order ID in format ORD followed by numbers"
    ),
    item_id: int = Path(
        ...,
        ge=1,
        le=100,
        description="Item ID between 1 and 100"
    )
):
    """
    Advanced path parameter validation with regex and constraints.
    
    This example shows complex validation:
    - String length constraints (min_length, max_length)
    - Regex pattern matching
    - Numeric range constraints (ge=greater equal, le=less equal)
    
    Args:
        order_id (str): Order ID matching pattern ORD followed by numbers
        item_id (int): Item ID between 1 and 100
        
    Returns:
        dict: Order item information
        
    Examples:
        GET /orders/ORD12345/items/5 -> Valid
        GET /orders/ABC123/items/5 -> Error: order_id doesn't match regex
        GET /orders/ORD12345/items/101 -> Error: item_id > 100
    """
    return {
        "order_id": order_id,
        "item_id": item_id,
        "item": f"Item {item_id} from order {order_id}",
        "validation_info": {
            "order_id_format": "ORD + numbers",
            "item_id_range": "1-100"
        }
    }

# 7. PATH PARAMETER WITH CUSTOM TYPE CONVERSION
@app.get("/dates/{date_str}")
def get_date_info(date_str: str = Path(..., regex=r"^\d{4}-\d{2}-\d{2}$")):
    """
    Path parameter with custom validation and conversion.
    
    This endpoint accepts dates in YYYY-MM-DD format and parses them.
    Shows how to handle custom type conversion and validation.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        dict: Date information and analysis
        
    Examples:
        GET /dates/2023-12-25 -> Valid date
        GET /dates/2023-13-01 -> Invalid month
        GET /dates/invalid -> Doesn't match regex pattern
    """
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        return {
            "input_date": date_str,
            "parsed_date": date_obj.isoformat(),
            "day_of_week": date_obj.strftime("%A"),
            "day_of_year": date_obj.timetuple().tm_yday,
            "is_weekend": date_obj.weekday() >= 5,
            "month_name": date_obj.strftime("%B")
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}"
        )

# 8. MULTIPLE PATH PARAMETERS WITH DIFFERENT TYPES
@app.get("/api/v{version:int}/users/{username}/posts/{post_slug}")
def get_versioned_post(
    version: int = Path(..., ge=1, le=3, description="API version (1-3)"),
    username: str = Path(..., min_length=3, max_length=20, description="Username"),
    post_slug: str = Path(..., regex=r"^[a-z0-9-]+$", description="Post slug (lowercase, numbers, hyphens)")
):
    """
    Complex endpoint with multiple validated path parameters.
    
    This demonstrates a realistic API endpoint with:
    - Version number validation
    - Username constraints
    - URL-friendly slug validation
    
    Args:
        version (int): API version (1-3)
        username (str): Username (3-20 characters)
        post_slug (str): URL slug (lowercase letters, numbers, hyphens)
        
    Returns:
        dict: Post information with API version context
        
    Examples:
        GET /api/v2/users/alice/posts/my-first-post -> Valid
        GET /api/v5/users/alice/posts/my-first-post -> Error: version > 3
        GET /api/v2/users/al/posts/my-first-post -> Error: username too short
        GET /api/v2/users/alice/posts/My-First-Post -> Error: slug has uppercase
    """
    return {
        "api_version": version,
        "username": username,
        "post_slug": post_slug,
        "post_title": post_slug.replace("-", " ").title(),
        "endpoint_info": {
            "version_supported": f"API v{version}",
            "username_valid": len(username) >= 3,
            "slug_format": "lowercase-with-hyphens"
        },
        "full_path": f"/api/v{version}/users/{username}/posts/{post_slug}"
    }

# ROOT ENDPOINT FOR NAVIGATION
@app.get("/")
def root():
    """
    Root endpoint listing all available path parameter examples.
    """
    return {
        "message": "FastAPI Path Parameters Tutorial",
        "examples": {
            "basic": "/users/1",
            "validation": "/users/1/posts/5",
            "file_path": "/files/docs/readme.txt",
            "enum": "/models/alexnet",
            "mixed": "/users/1/profile?include_posts=true",
            "advanced": "/orders/ORD12345/items/5",
            "date": "/dates/2023-12-25",
            "complex": "/api/v2/users/alice/posts/my-first-post"
        },
        "tips": [
            "Use type hints for automatic validation",
            "Path() function provides advanced validation options",
            "Enums restrict values to predefined choices",
            "Regex patterns validate string formats",
            "Combine path and query parameters for flexible APIs"
        ]
    }

# WHAT YOU'VE LEARNED:
"""
1. Path Parameters Basics:
   - {parameter_name} in URL path
   - Automatic type conversion
   - Required by default

2. Validation Options:
   - gt, ge, lt, le for numbers
   - min_length, max_length for strings
   - regex for pattern matching

3. Special Path Types:
   - {param:path} for paths with slashes
   - Enum for restricted choices
   - Custom validation functions

4. Best Practices:
   - Use descriptive parameter names
   - Add validation constraints
   - Provide clear documentation
   - Handle validation errors gracefully

5. Common Patterns:
   - /users/{user_id} - Resource by ID
   - /api/v{version} - API versioning
   - /files/{filepath:path} - File paths
   - /categories/{category_name} - Named resources

NEXT: Move to 04_query_parameters.py to learn about URL query parameters!
""" 