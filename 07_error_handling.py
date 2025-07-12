"""
🚨 FastAPI Error Handling - Managing Exceptions and Errors

This file teaches you everything about error handling in FastAPI:
- Custom exception classes and handlers
- Validation error handling
- HTTP exceptions and status codes
- Global error handling patterns
- Error response models

Run this file with: uvicorn 07_error_handling:app --reload
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ValidationError, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="FastAPI Error Handling Tutorial",
    description="Master error handling, custom exceptions, and error responses",
    version="1.0.0"
)

# LINE-BY-LINE EXPLANATION OF ERROR MODELS:

# 1. CUSTOM ERROR RESPONSE MODELS
class ErrorDetail(BaseModel):
    """
    Model for individual error details.
    
    This provides a structured way to represent error information
    including field-specific validation errors.
    """
    field: Optional[str] = None      # Field that caused the error (for validation errors)
    message: str                     # Human-readable error message
    code: Optional[str] = None       # Machine-readable error code
    value: Optional[Any] = None      # The value that caused the error

class ErrorResponse(BaseModel):
    """
    Standardized error response model.
    
    This model provides a consistent structure for all error responses
    across your API, making it easier for clients to handle errors.
    """
    error: bool = True               # Always True for error responses
    message: str                     # Main error message
    details: List[ErrorDetail] = []  # List of detailed error information
    error_code: Optional[str] = None # Application-specific error code
    timestamp: datetime = datetime.now()
    request_id: Optional[str] = None # For tracking and debugging

class ValidationErrorResponse(BaseModel):
    """
    Specific response model for validation errors.
    
    Used when request data doesn't meet validation requirements.
    """
    error: bool = True
    message: str = "Validation error"
    validation_errors: List[ErrorDetail]
    timestamp: datetime = datetime.now()

# 2. CUSTOM EXCEPTION CLASSES
class APIException(Exception):
    """
    Base custom exception class for API errors.
    
    This serves as the parent class for all custom exceptions in your API.
    It provides a consistent interface for error handling.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []
        super().__init__(self.message)

class UserNotFoundException(APIException):
    """
    Exception raised when a user is not found.
    
    Inherits from APIException and provides specific defaults for user-related errors.
    """
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User with ID {user_id} not found",
            status_code=404,
            error_code="USER_NOT_FOUND"
        )

class InsufficientPermissionsException(APIException):
    """Exception for permission-related errors."""
    def __init__(self, required_permission: str):
        super().__init__(
            message=f"Insufficient permissions. Required: {required_permission}",
            status_code=403,
            error_code="INSUFFICIENT_PERMISSIONS"
        )

class DuplicateResourceException(APIException):
    """Exception for duplicate resource creation attempts."""
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} with identifier '{identifier}' already exists",
            status_code=409,
            error_code="DUPLICATE_RESOURCE"
        )

class BusinessLogicException(APIException):
    """Exception for business logic violations."""
    def __init__(self, message: str, details: Optional[List[ErrorDetail]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details or []
        )

class ExternalServiceException(APIException):
    """Exception for external service failures."""
    def __init__(self, service_name: str, original_error: str):
        super().__init__(
            message=f"External service '{service_name}' is unavailable",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR"
        )

# 3. BUSINESS MODELS FOR EXAMPLES
class User(BaseModel):
    """User model with validation."""
    id: Optional[int] = None
    name: str
    email: str
    age: int
    password: str
    
    @validator('age')
    def validate_age(cls, v):
        if v < 0:
            raise ValueError('Age must be positive')
        if v > 150:
            raise ValueError('Age must be realistic (≤ 150)')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

class Account(BaseModel):
    """Account model for business logic examples."""
    id: Optional[int] = None
    user_id: int
    balance: float
    is_active: bool = True
    
    @validator('balance')
    def validate_balance(cls, v):
        if v < 0:
            raise ValueError('Balance cannot be negative')
        return v

# Mock databases
users_db = {}
accounts_db = {}
next_user_id = 1
next_account_id = 1

# LINE-BY-LINE EXPLANATION OF EXCEPTION HANDLERS:

# 1. CUSTOM EXCEPTION HANDLER
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """
    Global exception handler for custom API exceptions.
    
    This handler catches all APIException instances and converts them
    to standardized JSON responses. It provides consistent error formatting
    across your entire API.
    
    Args:
        request (Request): The incoming request object
        exc (APIException): The exception that was raised
        
    Returns:
        JSONResponse: Standardized error response
    """
    # Log the error for debugging
    logger.error(f"API Exception: {exc.message} | Status: {exc.status_code}")
    
    # Create standardized error response
    error_response = ErrorResponse(
        message=exc.message,
        details=exc.details,
        error_code=exc.error_code,
        request_id=str(id(request))  # Simple request ID for tracking
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

# 2. VALIDATION ERROR HANDLER
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for Pydantic validation errors.
    
    This handler catches validation errors that occur when request data
    doesn't meet the requirements defined in Pydantic models.
    
    Args:
        request (Request): The incoming request object
        exc (RequestValidationError): The validation error
        
    Returns:
        JSONResponse: Formatted validation error response
    """
    # Convert Pydantic errors to our error format
    error_details = []
    for error in exc.errors():
        error_detail = ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            code=error["type"],
            value=error.get("input")
        )
        error_details.append(error_detail)
    
    # Log validation errors
    logger.warning(f"Validation error on {request.url}: {len(error_details)} errors")
    
    # Create validation error response
    validation_response = ValidationErrorResponse(
        validation_errors=error_details
    )
    
    return JSONResponse(
        status_code=422,
        content=validation_response.dict()
    )

# 3. HTTP EXCEPTION HANDLER
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for FastAPI HTTP exceptions.
    
    This handler catches HTTPException instances and formats them
    consistently with our error response model.
    
    Args:
        request (Request): The incoming request object
        exc (HTTPException): The HTTP exception
        
    Returns:
        JSONResponse: Formatted HTTP error response
    """
    logger.warning(f"HTTP Exception: {exc.detail} | Status: {exc.status_code}")
    
    error_response = ErrorResponse(
        message=exc.detail,
        error_code=f"HTTP_{exc.status_code}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

# 4. GENERIC EXCEPTION HANDLER
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unexpected errors.
    
    This handler catches any exception that wasn't handled by other handlers.
    It provides a safe fallback and prevents internal server errors from
    exposing sensitive information.
    
    Args:
        request (Request): The incoming request object
        exc (Exception): The unexpected exception
        
    Returns:
        JSONResponse: Generic error response
    """
    # Log the full exception with traceback
    logger.error(f"Unexpected error: {str(exc)}\n{traceback.format_exc()}")
    
    # Don't expose internal error details in production
    error_response = ErrorResponse(
        message="An unexpected error occurred. Please try again later.",
        error_code="INTERNAL_SERVER_ERROR"
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

# LINE-BY-LINE EXPLANATION OF ERROR HANDLING ENDPOINTS:

# 1. BASIC ERROR HANDLING
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    Basic endpoint with custom exception handling.
    
    This demonstrates how to use custom exceptions in your endpoints.
    The exception handler will automatically format the error response.
    
    Args:
        user_id (int): User ID to retrieve
        
    Returns:
        dict: User data
        
    Raises:
        UserNotFoundException: When user is not found
    """
    if user_id not in users_db:
        # Raise custom exception - will be caught by exception handler
        raise UserNotFoundException(user_id)
    
    return users_db[user_id]

# 2. VALIDATION ERROR DEMONSTRATION
@app.post("/users")
async def create_user(user: User):
    """
    Endpoint that demonstrates validation error handling.
    
    This endpoint will trigger validation errors if the request data
    doesn't meet the User model requirements.
    
    Args:
        user (User): User data to create
        
    Returns:
        dict: Created user data
        
    Raises:
        DuplicateResourceException: When user email already exists
        RequestValidationError: When validation fails (handled automatically)
    """
    global next_user_id
    
    # Check for duplicate email
    for existing_user in users_db.values():
        if existing_user["email"] == user.email:
            raise DuplicateResourceException("User", user.email)
    
    # Create user
    user_data = user.dict()
    user_data["id"] = next_user_id
    user_data["created_at"] = datetime.now()
    
    users_db[next_user_id] = user_data
    next_user_id += 1
    
    # Remove password from response
    response_data = user_data.copy()
    del response_data["password"]
    
    return response_data

# 3. BUSINESS LOGIC ERROR HANDLING
@app.post("/accounts/{account_id}/withdraw")
async def withdraw_money(account_id: int, amount: float):
    """
    Endpoint demonstrating business logic error handling.
    
    This endpoint shows how to handle business rule violations
    with detailed error information.
    
    Args:
        account_id (int): Account ID to withdraw from
        amount (float): Amount to withdraw
        
    Returns:
        dict: Updated account information
        
    Raises:
        APIException: For various business logic violations
    """
    # Validate account exists
    if account_id not in accounts_db:
        raise APIException(
            message="Account not found",
            status_code=404,
            error_code="ACCOUNT_NOT_FOUND"
        )
    
    account = accounts_db[account_id]
    
    # Validate account is active
    if not account["is_active"]:
        raise APIException(
            message="Account is inactive",
            status_code=403,
            error_code="ACCOUNT_INACTIVE"
        )
    
    # Validate withdrawal amount
    if amount <= 0:
        raise BusinessLogicException(
            message="Invalid withdrawal amount",
            details=[
                ErrorDetail(
                    field="amount",
                    message="Amount must be positive",
                    code="INVALID_AMOUNT",
                    value=amount
                )
            ]
        )
    
    # Check sufficient funds
    if account["balance"] < amount:
        raise BusinessLogicException(
            message="Insufficient funds",
            details=[
                ErrorDetail(
                    field="balance",
                    message=f"Available balance: ${account['balance']:.2f}",
                    code="INSUFFICIENT_FUNDS",
                    value=account["balance"]
                )
            ]
        )
    
    # Perform withdrawal
    account["balance"] -= amount
    account["last_transaction"] = datetime.now()
    
    return {
        "message": "Withdrawal successful",
        "account_id": account_id,
        "amount": amount,
        "new_balance": account["balance"]
    }

# 4. MULTIPLE ERROR CONDITIONS
@app.put("/users/{user_id}/permissions")
async def update_user_permissions(user_id: int, permissions: List[str], admin_user_id: int):
    """
    Endpoint with multiple error conditions.
    
    This demonstrates handling multiple different error scenarios
    within a single endpoint.
    
    Args:
        user_id (int): User ID to update permissions for
        permissions (List[str]): List of permissions to grant
        admin_user_id (int): ID of admin user making the request
        
    Returns:
        dict: Updated user information
        
    Raises:
        UserNotFoundException: When user is not found
        InsufficientPermissionsException: When admin doesn't have permission
        BusinessLogicException: When permissions are invalid
    """
    # Validate target user exists
    if user_id not in users_db:
        raise UserNotFoundException(user_id)
    
    # Validate admin user exists
    if admin_user_id not in users_db:
        raise UserNotFoundException(admin_user_id)
    
    # Check admin permissions (simplified check)
    admin_user = users_db[admin_user_id]
    if admin_user.get("role") != "admin":
        raise InsufficientPermissionsException("admin role")
    
    # Validate permissions
    valid_permissions = {"read", "write", "delete", "admin"}
    invalid_permissions = set(permissions) - valid_permissions
    
    if invalid_permissions:
        error_details = [
            ErrorDetail(
                field="permissions",
                message=f"Invalid permission: {perm}",
                code="INVALID_PERMISSION",
                value=perm
            )
            for perm in invalid_permissions
        ]
        
        raise BusinessLogicException(
            message="Invalid permissions specified",
            details=error_details
        )
    
    # Update user permissions
    user = users_db[user_id]
    user["permissions"] = permissions
    user["updated_at"] = datetime.now()
    user["updated_by"] = admin_user_id
    
    return {
        "message": "Permissions updated successfully",
        "user_id": user_id,
        "permissions": permissions
    }

# 5. EXTERNAL SERVICE ERROR HANDLING
@app.get("/users/{user_id}/profile-picture")
async def get_user_profile_picture(user_id: int):
    """
    Endpoint demonstrating external service error handling.
    
    This shows how to handle errors from external services
    and provide meaningful error messages to clients.
    
    Args:
        user_id (int): User ID to get profile picture for
        
    Returns:
        dict: Profile picture information
        
    Raises:
        UserNotFoundException: When user is not found
        ExternalServiceException: When external service fails
    """
    # Validate user exists
    if user_id not in users_db:
        raise UserNotFoundException(user_id)
    
    # Simulate external service call
    try:
        # This would be a real external service call
        # For demo, we'll simulate a failure
        if user_id == 999:  # Simulate service failure
            raise Exception("Service timeout")
        
        # Simulate successful response
        return {
            "user_id": user_id,
            "profile_picture_url": f"https://example.com/pictures/{user_id}.jpg",
            "last_updated": datetime.now()
        }
    
    except Exception as e:
        # Convert external service error to our exception format
        raise ExternalServiceException("profile-picture-service", str(e))

# 6. CONDITIONAL ERROR HANDLING
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, force: bool = False):
    """
    Endpoint with conditional error handling.
    
    This demonstrates how to handle different error conditions
    based on request parameters.
    
    Args:
        user_id (int): User ID to delete
        force (bool): Whether to force deletion
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        UserNotFoundException: When user is not found
        BusinessLogicException: When deletion is not allowed
    """
    # Validate user exists
    if user_id not in users_db:
        raise UserNotFoundException(user_id)
    
    user = users_db[user_id]
    
    # Check if user has active accounts
    user_accounts = [acc for acc in accounts_db.values() if acc["user_id"] == user_id]
    active_accounts = [acc for acc in user_accounts if acc["is_active"]]
    
    if active_accounts and not force:
        raise BusinessLogicException(
            message="Cannot delete user with active accounts",
            details=[
                ErrorDetail(
                    field="active_accounts",
                    message=f"User has {len(active_accounts)} active accounts",
                    code="ACTIVE_ACCOUNTS_EXIST",
                    value=len(active_accounts)
                )
            ]
        )
    
    # Delete user
    del users_db[user_id]
    
    # Delete user accounts if forced
    if force:
        for account in user_accounts:
            if account["id"] in accounts_db:
                del accounts_db[account["id"]]
    
    return {
        "message": "User deleted successfully",
        "user_id": user_id,
        "forced": force
    }

# 7. ERROR TESTING ENDPOINTS
@app.get("/test-errors/{error_type}")
async def test_error_handling(error_type: str):
    """
    Endpoint for testing different error types.
    
    This endpoint allows you to test how different exceptions
    are handled by your error handlers.
    
    Args:
        error_type (str): Type of error to generate
        
    Returns:
        dict: Success response (if no error)
        
    Raises:
        Various exceptions based on error_type parameter
    """
    if error_type == "validation":
        # Trigger validation error
        raise RequestValidationError([{
            "loc": ("body", "field"),
            "msg": "Test validation error",
            "type": "value_error"
        }])
    
    elif error_type == "http":
        # Trigger HTTP exception
        raise HTTPException(
            status_code=400,
            detail="Test HTTP exception"
        )
    
    elif error_type == "custom":
        # Trigger custom exception
        raise APIException(
            message="Test custom exception",
            status_code=418,
            error_code="TEST_ERROR"
        )
    
    elif error_type == "unexpected":
        # Trigger unexpected exception
        raise ValueError("Test unexpected error")
    
    else:
        return {"message": f"No error triggered for type: {error_type}"}

# UTILITY ENDPOINTS

@app.post("/accounts")
async def create_account(account: Account):
    """Create account for testing business logic errors."""
    global next_account_id
    
    # Validate user exists
    if account.user_id not in users_db:
        raise UserNotFoundException(account.user_id)
    
    account_data = account.dict()
    account_data["id"] = next_account_id
    account_data["created_at"] = datetime.now()
    
    accounts_db[next_account_id] = account_data
    next_account_id += 1
    
    return account_data

@app.get("/")
def root():
    """Root endpoint with error handling examples."""
    return {
        "message": "FastAPI Error Handling Tutorial",
        "examples": {
            "user_not_found": "/users/999",
            "validation_error": "POST /users with invalid data",
            "business_logic_error": "/accounts/1/withdraw with invalid amount",
            "permission_error": "/users/1/permissions",
            "external_service_error": "/users/999/profile-picture",
            "conditional_error": "/users/1 (DELETE)",
            "test_errors": "/test-errors/validation"
        },
        "error_handling_features": {
            "custom_exceptions": "Domain-specific exception classes",
            "exception_handlers": "Global error handling",
            "validation_errors": "Pydantic validation error formatting",
            "business_logic_errors": "Detailed business rule violation errors",
            "external_service_errors": "Handle third-party service failures",
            "error_response_models": "Consistent error response structure",
            "logging": "Comprehensive error logging",
            "request_tracking": "Request ID for debugging"
        }
    }

# WHAT YOU'VE LEARNED:
"""
1. Error Handling Fundamentals:
   - Custom exception classes for domain-specific errors
   - Global exception handlers for consistent error responses
   - Error response models for structured error information
   - Logging and debugging support

2. Exception Types:
   - APIException: Base class for custom API errors
   - HTTPException: Standard HTTP errors
   - RequestValidationError: Pydantic validation errors
   - BusinessLogicException: Business rule violations

3. Error Response Structure:
   - Consistent error response format
   - Detailed error information with field-level details
   - Error codes for machine-readable error identification
   - Timestamps and request tracking

4. Error Handling Patterns:
   - Resource not found errors
   - Validation and data format errors
   - Business logic and rule violations
   - Permission and authorization errors
   - External service failures
   - Conditional error handling

5. Best Practices:
   - Use specific exception types for different error scenarios
   - Provide detailed error information without exposing internals
   - Log errors for debugging and monitoring
   - Use consistent error response structure
   - Handle both expected and unexpected errors gracefully

6. Production Considerations:
   - Don't expose sensitive information in error messages
   - Log all errors for debugging
   - Provide request tracking for support
   - Use appropriate HTTP status codes
   - Handle external service failures gracefully

NEXT: Move to 08_dependency_injection.py to learn about FastAPI's dependency system!
""" 