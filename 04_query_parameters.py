"""
🔍 FastAPI Query Parameters - URL Search and Filter Parameters

This file teaches you everything about query parameters in FastAPI:
- Basic query parameters
- Optional and required query parameters
- Type validation and conversion
- Multiple values and lists
- Complex filtering and pagination

Run this file with: uvicorn 04_query_parameters:app --reload
"""

from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Union
from enum import Enum
from datetime import datetime, date
from pydantic import BaseModel

# Create FastAPI application
app = FastAPI(
    title="FastAPI Query Parameters Tutorial",
    description="Master query parameters with validation and advanced features",
    version="1.0.0"
)

# ENUMS FOR QUERY PARAMETER VALIDATION
class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class ItemStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"

# Mock database for examples
products_db = [
    {"id": 1, "name": "Laptop", "price": 999.99, "category": "electronics", "tags": ["computer", "work"], "status": "active"},
    {"id": 2, "name": "Coffee Mug", "price": 15.99, "category": "home", "tags": ["kitchen", "ceramic"], "status": "active"},
    {"id": 3, "name": "Running Shoes", "price": 89.99, "category": "sports", "tags": ["footwear", "running"], "status": "inactive"},
    {"id": 4, "name": "Smartphone", "price": 699.99, "category": "electronics", "tags": ["mobile", "communication"], "status": "active"},
    {"id": 5, "name": "Backpack", "price": 49.99, "category": "travel", "tags": ["bag", "travel"], "status": "pending"},
]

# LINE-BY-LINE EXPLANATION OF QUERY PARAMETERS:

# 1. BASIC QUERY PARAMETERS
@app.get("/items")
def get_items(skip: int = 0, limit: int = 10):
    """
    Basic query parameters for pagination.
    
    Query parameters come after the ? in the URL and are separated by &.
    They are automatically parsed from the URL query string.
    
    Args:
        skip (int): Number of items to skip (default: 0)
        limit (int): Maximum number of items to return (default: 10)
        
    Returns:
        dict: Paginated list of items
        
    Examples:
        GET /items -> skip=0, limit=10 (defaults)
        GET /items?skip=5 -> skip=5, limit=10
        GET /items?skip=0&limit=5 -> skip=0, limit=5
        GET /items?limit=20&skip=10 -> skip=10, limit=20 (order doesn't matter)
    """
    # Query parameters are automatically converted to the specified types
    # If conversion fails, FastAPI returns a 422 validation error
    
    total_items = len(products_db)
    items = products_db[skip:skip + limit]
    
    return {
        "items": items,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total_items,
            "returned": len(items)
        }
    }

# 2. OPTIONAL QUERY PARAMETERS
@app.get("/search")
def search_products(
    q: Optional[str] = None,           # Optional search query
    category: Optional[str] = None,    # Optional category filter
    min_price: Optional[float] = None, # Optional minimum price
    max_price: Optional[float] = None  # Optional maximum price
):
    """
    Optional query parameters for flexible searching.
    
    Optional parameters have default values (usually None) and are only
    applied when provided in the request.
    
    Args:
        q: Search query for product names (optional)
        category: Filter by category (optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
        
    Returns:
        dict: Filtered search results
        
    Examples:
        GET /search -> No filters (returns all)
        GET /search?q=laptop -> Search for "laptop"
        GET /search?category=electronics -> Filter by electronics
        GET /search?min_price=50&max_price=100 -> Price range filter
        GET /search?q=shoes&category=sports&min_price=80 -> Combined filters
    """
    # Start with all products
    results = products_db.copy()
    filters_applied = []
    
    # Apply search query if provided
    if q is not None:
        results = [p for p in results if q.lower() in p["name"].lower()]
        filters_applied.append(f"name contains '{q}'")
    
    # Apply category filter if provided
    if category is not None:
        results = [p for p in results if p["category"] == category]
        filters_applied.append(f"category = '{category}'")
    
    # Apply price range filters if provided
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
        filters_applied.append(f"price >= {min_price}")
    
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
        filters_applied.append(f"price <= {max_price}")
    
    return {
        "results": results,
        "count": len(results),
        "filters_applied": filters_applied,
        "query_parameters": {
            "q": q,
            "category": category,
            "min_price": min_price,
            "max_price": max_price
        }
    }

# 3. QUERY PARAMETERS WITH VALIDATION
@app.get("/products/paginated")
def get_paginated_products(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page (1-100)"),
    sort_by: str = Query("id", regex="^(id|name|price)$", description="Sort field"),
    order: SortOrder = Query(SortOrder.asc, description="Sort order")
):
    """
    Query parameters with advanced validation using Query().
    
    The Query() function provides validation, documentation, and constraints:
    - ge, le: Greater/less than or equal (for numbers)
    - regex: Pattern matching for strings
    - Enum: Restricted to predefined values
    
    Args:
        page (int): Page number (>= 1)
        size (int): Items per page (1-100)
        sort_by (str): Field to sort by (id, name, or price)
        order (SortOrder): Sort order (asc or desc)
        
    Returns:
        dict: Paginated and sorted products
        
    Examples:
        GET /products/paginated -> Default values
        GET /products/paginated?page=2&size=5 -> Page 2, 5 items per page
        GET /products/paginated?sort_by=price&order=desc -> Sort by price descending
        GET /products/paginated?page=0 -> Error: page must be >= 1
        GET /products/paginated?size=200 -> Error: size must be <= 100
        GET /products/paginated?sort_by=invalid -> Error: doesn't match regex
    """
    # Calculate offset for pagination
    offset = (page - 1) * size
    
    # Sort products
    reverse = (order == SortOrder.desc)
    sorted_products = sorted(products_db, key=lambda x: x[sort_by], reverse=reverse)
    
    # Apply pagination
    paginated_products = sorted_products[offset:offset + size]
    
    # Calculate pagination metadata
    total_items = len(products_db)
    total_pages = (total_items + size - 1) // size  # Ceiling division
    
    return {
        "products": paginated_products,
        "pagination": {
            "page": page,
            "size": size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        },
        "sorting": {
            "sort_by": sort_by,
            "order": order.value
        }
    }

# 4. LIST QUERY PARAMETERS
@app.get("/products/filter")
def filter_products(
    tags: List[str] = Query([], description="Filter by tags (can specify multiple)"),
    categories: List[str] = Query([], description="Filter by categories (can specify multiple)"),
    statuses: List[ItemStatus] = Query([ItemStatus.active], description="Filter by status")
):
    """
    Query parameters that accept multiple values as lists.
    
    Lists in query parameters can be specified in multiple ways:
    - Multiple parameters: ?tags=tag1&tags=tag2
    - Comma-separated: ?tags=tag1,tag2 (depends on client)
    
    Args:
        tags (List[str]): List of tags to filter by
        categories (List[str]): List of categories to filter by
        statuses (List[ItemStatus]): List of statuses to filter by
        
    Returns:
        dict: Filtered products
        
    Examples:
        GET /products/filter -> Default filters (active status only)
        GET /products/filter?tags=computer&tags=work -> Filter by multiple tags
        GET /products/filter?categories=electronics&categories=sports -> Multiple categories
        GET /products/filter?statuses=active&statuses=pending -> Multiple statuses
    """
    results = products_db.copy()
    
    # Filter by tags (product must have at least one of the specified tags)
    if tags:
        results = [
            p for p in results 
            if any(tag in p["tags"] for tag in tags)
        ]
    
    # Filter by categories (product category must be in the list)
    if categories:
        results = [p for p in results if p["category"] in categories]
    
    # Filter by statuses (product status must be in the list)
    status_values = [status.value for status in statuses]
    results = [p for p in results if p["status"] in status_values]
    
    return {
        "products": results,
        "count": len(results),
        "filters": {
            "tags": tags,
            "categories": categories,
            "statuses": [status.value for status in statuses]
        }
    }

# 5. BOOLEAN QUERY PARAMETERS
@app.get("/products/special")
def get_special_products(
    on_sale: bool = Query(False, description="Show only products on sale"),
    include_inactive: bool = Query(False, description="Include inactive products"),
    premium_only: bool = Query(False, description="Show only premium products (price > 500)")
):
    """
    Boolean query parameters for toggle-like filtering.
    
    Boolean parameters accept various string representations:
    - true, True, 1, yes, on -> True
    - false, False, 0, no, off -> False
    
    Args:
        on_sale (bool): Filter for sale products
        include_inactive (bool): Whether to include inactive products
        premium_only (bool): Show only premium products
        
    Returns:
        dict: Filtered products based on boolean flags
        
    Examples:
        GET /products/special -> All defaults (false)
        GET /products/special?on_sale=true -> Only sale products
        GET /products/special?include_inactive=1 -> Include inactive
        GET /products/special?premium_only=yes -> Only premium products
        GET /products/special?on_sale=true&premium_only=true -> Combined filters
    """
    results = products_db.copy()
    
    # For demo purposes, let's assume products with even IDs are on sale
    if on_sale:
        results = [p for p in results if p["id"] % 2 == 0]
    
    # Include/exclude inactive products
    if not include_inactive:
        results = [p for p in results if p["status"] != "inactive"]
    
    # Filter for premium products
    if premium_only:
        results = [p for p in results if p["price"] > 500]
    
    return {
        "products": results,
        "count": len(results),
        "filters": {
            "on_sale": on_sale,
            "include_inactive": include_inactive,
            "premium_only": premium_only
        }
    }

# 6. DATE AND TIME QUERY PARAMETERS
@app.get("/analytics/sales")
def get_sales_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: str = Query("day", regex="^(hour|day|week|month)$", description="Data granularity")
):
    """
    Date and time query parameters with automatic parsing.
    
    FastAPI automatically parses ISO date strings (YYYY-MM-DD) to date objects.
    Invalid date formats will result in 422 validation errors.
    
    Args:
        start_date (date): Start date for analytics
        end_date (date): End date for analytics
        granularity (str): Time granularity for data aggregation
        
    Returns:
        dict: Mock analytics data
        
    Examples:
        GET /analytics/sales -> No date filter
        GET /analytics/sales?start_date=2023-01-01 -> From specific date
        GET /analytics/sales?start_date=2023-01-01&end_date=2023-12-31 -> Date range
        GET /analytics/sales?granularity=month -> Monthly granularity
        GET /analytics/sales?start_date=invalid-date -> Error: invalid date format
    """
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date"
        )
    
    # Mock analytics data
    analytics = {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "granularity": granularity
        },
        "metrics": {
            "total_sales": 15420.50,
            "orders_count": 147,
            "average_order_value": 104.90
        },
        "note": "This is mock data for demonstration purposes"
    }
    
    return analytics

# 7. UNION TYPE QUERY PARAMETERS
@app.get("/products/search-advanced")
def advanced_search(
    query: Union[str, int] = Query(..., description="Search by name or ID"),
    price_range: Optional[str] = Query(None, regex=r"^\d+(-\d+)?$", description="Price range (e.g., '100' or '100-500')")
):
    """
    Query parameters with Union types for flexible input.
    
    Union types allow a parameter to accept multiple types.
    FastAPI will try to convert to the first matching type.
    
    Args:
        query (Union[str, int]): Search query (name or product ID)
        price_range (str): Price range in format "min" or "min-max"
        
    Returns:
        dict: Search results
        
    Examples:
        GET /products/search-advanced?query=laptop -> Search by name
        GET /products/search-advanced?query=123 -> Search by ID
        GET /products/search-advanced?query=shoes&price_range=50-100 -> Name + price range
        GET /products/search-advanced?query=1&price_range=500 -> ID + minimum price
    """
    results = products_db.copy()
    
    # Handle query parameter (string or int)
    if isinstance(query, int):
        # Search by ID
        results = [p for p in results if p["id"] == query]
        search_type = "ID"
    else:
        # Search by name
        results = [p for p in results if query.lower() in p["name"].lower()]
        search_type = "name"
    
    # Handle price range if provided
    if price_range:
        if "-" in price_range:
            # Range format: "min-max"
            min_price, max_price = map(float, price_range.split("-"))
            results = [p for p in results if min_price <= p["price"] <= max_price]
            price_filter = f"{min_price}-{max_price}"
        else:
            # Single value format: "min"
            min_price = float(price_range)
            results = [p for p in results if p["price"] >= min_price]
            price_filter = f">={min_price}"
    else:
        price_filter = None
    
    return {
        "results": results,
        "count": len(results),
        "search_info": {
            "query": query,
            "search_type": search_type,
            "price_filter": price_filter
        }
    }

# 8. COMPLEX QUERY COMBINATIONS
@app.get("/products/complex-filter")
def complex_product_filter(
    # Basic filters
    name: Optional[str] = Query(None, min_length=2, description="Product name filter"),
    category: Optional[str] = Query(None, description="Product category"),
    
    # Price filters
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    
    # List filters
    tags: List[str] = Query([], description="Required tags"),
    exclude_tags: List[str] = Query([], description="Tags to exclude"),
    
    # Sorting and pagination
    sort_by: str = Query("id", regex="^(id|name|price)$"),
    sort_order: SortOrder = Query(SortOrder.asc),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    
    # Boolean filters
    active_only: bool = Query(True, description="Show only active products")
):
    """
    Complex query parameter combination demonstrating real-world API filtering.
    
    This endpoint combines all types of query parameters for comprehensive filtering,
    sorting, and pagination - typical of real e-commerce or catalog APIs.
    
    Returns:
        dict: Comprehensively filtered and paginated products
    """
    results = products_db.copy()
    applied_filters = []
    
    # Apply all filters
    if name:
        results = [p for p in results if name.lower() in p["name"].lower()]
        applied_filters.append(f"name contains '{name}'")
    
    if category:
        results = [p for p in results if p["category"] == category]
        applied_filters.append(f"category = '{category}'")
    
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
        applied_filters.append(f"price >= {min_price}")
    
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
        applied_filters.append(f"price <= {max_price}")
    
    if tags:
        results = [p for p in results if all(tag in p["tags"] for tag in tags)]
        applied_filters.append(f"includes tags: {tags}")
    
    if exclude_tags:
        results = [p for p in results if not any(tag in p["tags"] for tag in exclude_tags)]
        applied_filters.append(f"excludes tags: {exclude_tags}")
    
    if active_only:
        results = [p for p in results if p["status"] == "active"]
        applied_filters.append("status = active")
    
    # Validate price range
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(400, "min_price cannot be greater than max_price")
    
    # Sort results
    reverse = (sort_order == SortOrder.desc)
    results = sorted(results, key=lambda x: x[sort_by], reverse=reverse)
    
    # Pagination
    total_items = len(results)
    offset = (page - 1) * page_size
    paginated_results = results[offset:offset + page_size]
    
    return {
        "products": paginated_results,
        "metadata": {
            "total_items": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_items + page_size - 1) // page_size,
            "applied_filters": applied_filters,
            "sorting": {"field": sort_by, "order": sort_order.value}
        }
    }

# ROOT ENDPOINT
@app.get("/")
def root():
    """Root endpoint with examples and documentation."""
    return {
        "message": "FastAPI Query Parameters Tutorial",
        "examples": {
            "basic_pagination": "/items?skip=5&limit=10",
            "search": "/search?q=laptop&category=electronics&min_price=500",
            "validated_pagination": "/products/paginated?page=2&size=5&sort_by=price&order=desc",
            "list_filters": "/products/filter?tags=computer&tags=work&statuses=active",
            "boolean_filters": "/products/special?on_sale=true&premium_only=true",
            "date_range": "/analytics/sales?start_date=2023-01-01&end_date=2023-12-31",
            "advanced_search": "/products/search-advanced?query=laptop&price_range=500-1000",
            "complex_filter": "/products/complex-filter?name=laptop&min_price=500&sort_by=price&sort_order=desc"
        },
        "query_parameter_types": {
            "optional": "Have default values, not required",
            "required": "Must be provided (use Query(...) or no default)",
            "validated": "Use Query() with constraints",
            "lists": "Accept multiple values",
            "booleans": "Accept true/false values",
            "dates": "Automatically parsed from ISO format",
            "enums": "Restricted to predefined values"
        }
    }

# WHAT YOU'VE LEARNED:
"""
1. Query Parameter Basics:
   - Automatically parsed from URL query string
   - Type conversion and validation
   - Optional vs required parameters

2. Query() Function Features:
   - Validation constraints (ge, le, min_length, max_length)
   - Regex pattern matching
   - Documentation and descriptions
   - Default values

3. Advanced Types:
   - Lists for multiple values
   - Enums for restricted choices
   - Dates with automatic parsing
   - Union types for flexible input
   - Boolean parameters

4. Real-world Patterns:
   - Pagination (skip/limit or page/size)
   - Filtering and searching
   - Sorting with order
   - Date range queries
   - Complex combinations

5. Best Practices:
   - Provide sensible defaults
   - Validate input ranges
   - Use descriptive parameter names
   - Document parameter purposes
   - Handle edge cases (invalid ranges, etc.)

NEXT: Move to 05_request_body.py to learn about POST request bodies and Pydantic models!
""" 