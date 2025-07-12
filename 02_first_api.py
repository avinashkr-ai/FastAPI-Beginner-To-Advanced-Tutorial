"""
🔥 FastAPI First API - HTTP Methods and Status Codes

This file teaches you about different HTTP methods (GET, POST, PUT, DELETE)
and how to handle them in FastAPI with proper status codes and responses.

Run this file with: uvicorn 02_first_api:app --reload
"""

# Import necessary modules and classes
from fastapi import FastAPI, HTTPException, status  # HTTPException for custom errors, status for HTTP codes
from pydantic import BaseModel  # For data validation and serialization
from typing import List, Optional  # For type hints
from datetime import datetime  # For timestamps

# Create the FastAPI application instance
app = FastAPI(
    title="FastAPI HTTP Methods Demo",
    description="Learn all HTTP methods with detailed examples",
    version="1.0.0"
)

# LINE-BY-LINE EXPLANATION OF PYDANTIC MODELS:

# Define a Pydantic model for data validation
# Pydantic models automatically validate incoming data and convert types
class Item(BaseModel):
    """
    Pydantic model for Item data validation.
    
    This class defines the structure and validation rules for Item objects.
    FastAPI uses this to automatically validate request bodies and generate docs.
    """
    # Each field has a type annotation for automatic validation
    name: str                           # Required string field
    description: Optional[str] = None   # Optional string field with default None
    price: float                        # Required float field (will validate it's a number)
    tax: Optional[float] = None        # Optional float field
    tags: List[str] = []               # List of strings with empty list as default

# Model for updating items (all fields optional)
class ItemUpdate(BaseModel):
    """
    Model for partial item updates.
    All fields are optional so you can update just specific fields.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    tax: Optional[float] = None
    tags: Optional[List[str]] = None

# In-memory storage for demonstration (in real apps, use a database)
# This dictionary simulates a database
items_db = {}  # Will store items with ID as key

# LINE-BY-LINE EXPLANATION OF HTTP METHODS:

# 1. GET METHOD - Retrieve data
@app.get("/", tags=["Root"])  # tags organize endpoints in documentation
def read_root():
    """
    Root endpoint that explains the API.
    
    GET is used for retrieving data without side effects.
    This endpoint is idempotent (calling it multiple times has the same effect).
    """
    return {
        "message": "Welcome to FastAPI HTTP Methods Demo!",
        "available_endpoints": {
            "GET /items": "Get all items",
            "GET /items/{item_id}": "Get specific item",
            "POST /items": "Create new item",
            "PUT /items/{item_id}": "Update entire item",
            "PATCH /items/{item_id}": "Partially update item",
            "DELETE /items/{item_id}": "Delete item"
        }
    }

# GET - Retrieve all items
@app.get("/items", response_model=List[Item], tags=["Items"])
def get_all_items():
    """
    Retrieve all items from storage.
    
    Returns:
        List[Item]: List of all items in the database
        
    The response_model parameter tells FastAPI what the response should look like
    and automatically generates the correct documentation.
    """
    # Convert the items_db dictionary to a list of items
    return list(items_db.values())

# GET - Retrieve a specific item by ID
@app.get("/items/{item_id}", response_model=Item, tags=["Items"])
def get_item(item_id: int):
    """
    Retrieve a specific item by its ID.
    
    Args:
        item_id (int): The unique identifier of the item
        
    Returns:
        Item: The requested item
        
    Raises:
        HTTPException: 404 if item not found
    """
    # Check if item exists in our "database"
    if item_id not in items_db:
        # Raise an HTTP 404 error if item doesn't exist
        # FastAPI automatically converts this to a proper HTTP response
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,  # 404 status code
            detail=f"Item with id {item_id} not found"  # Error message
        )
    
    return items_db[item_id]

# 2. POST METHOD - Create new data
@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item: Item):
    """
    Create a new item.
    
    POST is used for creating new resources.
    The request body is automatically validated against the Item model.
    
    Args:
        item (Item): The item data from request body
        
    Returns:
        Item: The created item with assigned ID
        
    The status_code parameter sets the default success status code (201 for creation).
    """
    # Generate a new ID (in real apps, this would be handled by the database)
    item_id = len(items_db) + 1
    
    # Convert Pydantic model to dictionary and add metadata
    item_dict = item.dict()  # Convert to dict
    item_dict["id"] = item_id  # Add ID
    item_dict["created_at"] = datetime.now().isoformat()  # Add timestamp
    
    # Store in our "database"
    items_db[item_id] = item_dict
    
    return item_dict

# 3. PUT METHOD - Replace entire resource
@app.put("/items/{item_id}", response_model=Item, tags=["Items"])
def update_item(item_id: int, item: Item):
    """
    Replace an entire item with new data.
    
    PUT is used for complete replacement of a resource.
    All fields must be provided (unlike PATCH).
    
    Args:
        item_id (int): ID of the item to update
        item (Item): Complete new item data
        
    Returns:
        Item: The updated item
        
    Raises:
        HTTPException: 404 if item not found
    """
    # Check if item exists
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    # Replace the entire item (keeping original ID and created_at)
    updated_item = item.dict()
    updated_item["id"] = item_id
    updated_item["created_at"] = items_db[item_id].get("created_at")  # Keep original timestamp
    updated_item["updated_at"] = datetime.now().isoformat()  # Add update timestamp
    
    items_db[item_id] = updated_item
    return updated_item

# 4. PATCH METHOD - Partial update
@app.patch("/items/{item_id}", response_model=Item, tags=["Items"])
def patch_item(item_id: int, item_update: ItemUpdate):
    """
    Partially update an item.
    
    PATCH is used for partial updates where only specified fields are changed.
    Only provided fields will be updated, others remain unchanged.
    
    Args:
        item_id (int): ID of the item to update
        item_update (ItemUpdate): Partial item data (only fields to update)
        
    Returns:
        Item: The updated item
        
    Raises:
        HTTPException: 404 if item not found
    """
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    # Get existing item
    existing_item = items_db[item_id].copy()
    
    # Update only provided fields
    update_data = item_update.dict(exclude_unset=True)  # exclude_unset=True ignores None values
    for field, value in update_data.items():
        existing_item[field] = value
    
    # Add update timestamp
    existing_item["updated_at"] = datetime.now().isoformat()
    
    items_db[item_id] = existing_item
    return existing_item

# 5. DELETE METHOD - Remove resource
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
def delete_item(item_id: int):
    """
    Delete an item.
    
    DELETE is used for removing resources.
    Returns 204 No Content on successful deletion.
    
    Args:
        item_id (int): ID of the item to delete
        
    Raises:
        HTTPException: 404 if item not found
    """
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    # Delete the item
    del items_db[item_id]
    
    # For DELETE, we typically return no content (status 204)
    # FastAPI will automatically return an empty response with 204 status

# ADDITIONAL ENDPOINTS FOR LEARNING:

# GET with query parameters and filtering
@app.get("/items/search/", tags=["Search"])
def search_items(
    name: Optional[str] = None,           # Optional query parameter
    min_price: Optional[float] = None,    # Optional minimum price filter
    max_price: Optional[float] = None,    # Optional maximum price filter
    tags: Optional[str] = None            # Optional tags filter (comma-separated)
):
    """
    Search items with various filters.
    
    Query parameters allow clients to filter and customize the response.
    
    Args:
        name: Filter by item name (partial match)
        min_price: Minimum price filter
        max_price: Maximum price filter
        tags: Comma-separated tags to filter by
        
    Returns:
        List[dict]: Filtered items
        
    Example:
        GET /items/search/?name=laptop&min_price=500&max_price=1500
    """
    # Start with all items
    results = list(items_db.values())
    
    # Apply filters if provided
    if name:
        results = [item for item in results if name.lower() in item["name"].lower()]
    
    if min_price is not None:
        results = [item for item in results if item["price"] >= min_price]
    
    if max_price is not None:
        results = [item for item in results if item["price"] <= max_price]
    
    if tags:
        search_tags = [tag.strip() for tag in tags.split(",")]
        results = [
            item for item in results 
            if any(tag in item.get("tags", []) for tag in search_tags)
        ]
    
    return {
        "items": results,
        "count": len(results),
        "filters_applied": {
            "name": name,
            "min_price": min_price,
            "max_price": max_price,
            "tags": tags
        }
    }

# Endpoint that demonstrates different status codes
@app.get("/status-demo/{code}", tags=["Status Codes"])
def status_code_demo(code: int):
    """
    Demonstrate different HTTP status codes.
    
    This endpoint returns different responses based on the requested code.
    Useful for understanding HTTP status codes.
    
    Args:
        code (int): The status code to return
        
    Returns:
        dict: Response with information about the status code
    """
    status_messages = {
        200: "OK - Request successful",
        201: "Created - Resource created successfully",
        204: "No Content - Request successful, no response body",
        400: "Bad Request - Invalid request syntax",
        401: "Unauthorized - Authentication required",
        403: "Forbidden - Access denied",
        404: "Not Found - Resource not found",
        500: "Internal Server Error - Server error"
    }
    
    if code in status_messages:
        if code >= 400:  # Error codes
            raise HTTPException(
                status_code=code,
                detail=status_messages[code]
            )
        else:  # Success codes
            return {
                "status_code": code,
                "message": status_messages[code],
                "timestamp": datetime.now().isoformat()
            }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Status code {code} not supported in this demo"
        )

# WHAT YOU'VE LEARNED:
"""
1. HTTP Methods:
   - GET: Retrieve data (safe, idempotent)
   - POST: Create new resources
   - PUT: Replace entire resources
   - PATCH: Partial updates
   - DELETE: Remove resources

2. Status Codes:
   - 200: OK
   - 201: Created
   - 204: No Content
   - 400: Bad Request
   - 404: Not Found
   - 500: Internal Server Error

3. Pydantic Models:
   - Automatic validation
   - Type conversion
   - Documentation generation
   - Serialization/deserialization

4. FastAPI Features:
   - Automatic API documentation
   - Request/response validation
   - Error handling
   - Type hints

NEXT: Move to 03_path_parameters.py to learn about URL parameters and validation!
""" 