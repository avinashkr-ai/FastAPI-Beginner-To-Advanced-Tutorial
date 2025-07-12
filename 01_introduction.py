"""
🚀 FastAPI Introduction - Your First Step into Modern API Development

This file introduces you to FastAPI and explains every line of code.
FastAPI is a modern, fast web framework for building APIs with Python 3.7+.

Key Features:
- Fast: Very high performance, on par with NodeJS and Go
- Fast to code: Increase development speed by 200% to 300%
- Fewer bugs: Reduce human-induced errors by 40%
- Intuitive: Great editor support with auto-completion
- Easy: Designed to be easy to use and learn
- Short: Minimize code duplication
- Robust: Get production-ready code with automatic interactive documentation
- Standards-based: Based on open standards for APIs: OpenAPI and JSON Schema

Run this file with: uvicorn 01_introduction:app --reload
"""

# LINE-BY-LINE EXPLANATION:

# Line 1: Import the FastAPI class from the fastapi module
# FastAPI is the main class that creates your web application instance
from fastapi import FastAPI

# Line 2: Create an instance of the FastAPI application
# This 'app' object will be your main application that handles all API requests
# The app instance contains all your routes, middleware, and configuration
app = FastAPI(
    title="FastAPI Learning - Introduction",        # Sets the API title in the documentation
    description="Your first FastAPI application",   # Description shown in the docs
    version="1.0.0"                                # Version of your API
)

# Line 3: Define your first API endpoint (route)
# @app.get() is a decorator that tells FastAPI this function handles GET requests
# The "/" means this endpoint responds to the root URL (http://localhost:8000/)
@app.get("/")
def read_root():
    """
    This is your first API endpoint!
    
    When someone visits http://localhost:8000/, this function will run
    and return the dictionary below as JSON.
    
    Returns:
        dict: A simple greeting message
    """
    # This function returns a Python dictionary
    # FastAPI automatically converts it to JSON format
    return {"message": "Hello World! Welcome to FastAPI! 🚀"}

# Line 4: Another endpoint that demonstrates path parameters
# The {item_id} in the path is a path parameter that gets passed to the function
@app.get("/items/{item_id}")
def read_item(item_id: int):
    """
    This endpoint demonstrates path parameters.
    
    Args:
        item_id (int): The ID of the item to retrieve
        
    Returns:
        dict: Item information
        
    Example:
        GET /items/42 -> {"item_id": 42, "message": "This is item number 42"}
    """
    # item_id is automatically converted to an integer by FastAPI
    # If someone sends a non-integer, FastAPI will return a validation error
    return {"item_id": item_id, "message": f"This is item number {item_id}"}

# Line 5: Endpoint with query parameters
@app.get("/hello")
def say_hello(name: str = "World", age: int = None):
    """
    This endpoint demonstrates query parameters.
    
    Args:
        name (str): Name to greet (default: "World")
        age (int): Optional age parameter
        
    Returns:
        dict: Personalized greeting
        
    Examples:
        GET /hello -> {"greeting": "Hello, World!"}
        GET /hello?name=Alice -> {"greeting": "Hello, Alice!"}
        GET /hello?name=Bob&age=25 -> {"greeting": "Hello, Bob!", "age": 25}
    """
    response = {"greeting": f"Hello, {name}!"}
    
    # If age is provided, add it to the response
    if age is not None:
        response["age"] = age
        response["message"] = f"{name} is {age} years old"
    
    return response

# Line 6: Health check endpoint (common in production APIs)
@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and deployment.
    
    This is a common pattern in production APIs to check if the service is running.
    
    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "FastAPI Learning App",
        "version": "1.0.0"
    }

# WHAT HAPPENS WHEN YOU RUN THIS FILE:
"""
1. FastAPI creates an ASGI application instance
2. It scans for all the @app decorators to register routes
3. It automatically generates OpenAPI documentation
4. Uvicorn starts an ASGI server to serve your application
5. Your API becomes available at http://localhost:8000

AUTOMATIC FEATURES YOU GET:
- Interactive API documentation at http://localhost:8000/docs (Swagger UI)
- Alternative documentation at http://localhost:8000/redoc
- JSON schema at http://localhost:8000/openapi.json
- Automatic request/response validation
- Type hints for better IDE support
- Error handling and HTTP status codes

HOW TO TEST:
1. Run: uvicorn 01_introduction:app --reload
2. Open http://localhost:8000/docs in your browser
3. Try the endpoints directly or use the interactive docs
"""

# NEXT STEPS:
# After understanding this basic structure, move to 02_first_api.py
# to learn more about different HTTP methods and request/response handling 