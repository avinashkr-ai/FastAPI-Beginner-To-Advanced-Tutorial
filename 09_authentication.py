"""
🔐 FastAPI Authentication & Security - Complete Security Implementation

This file teaches you everything about authentication and security in FastAPI:
- JWT token authentication
- OAuth2 with password flow
- API key authentication
- Role-based access control
- Security best practices

Run this file with: uvicorn 09_authentication:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="FastAPI Authentication & Security Tutorial",
    description="Complete authentication and security implementation",
    version="1.0.0"
)

# Add CORS middleware for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React/Vue.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE-BY-LINE EXPLANATION OF SECURITY CONFIGURATION:

# 1. JWT CONFIGURATION
SECRET_KEY = "your-secret-key-here-make-it-long-and-random"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 2. PASSWORD HASHING
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password.
    
    Args:
        plain_password (str): Plain text password
        hashed_password (str): Hashed password from database
        
    Returns:
        bool: True if passwords match
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

# 3. OAUTH2 SCHEME
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",  # URL where clients can get tokens
    scopes={
        "read": "Read access",
        "write": "Write access", 
        "admin": "Admin access"
    }
)

# 4. HTTP BEARER SCHEME
security = HTTPBearer(auto_error=False)

# LINE-BY-LINE EXPLANATION OF DATA MODELS:

# 1. USER MODELS
class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    """User creation model with password."""
    password: str

class UserInDB(UserBase):
    """User model as stored in database."""
    id: int
    hashed_password: str
    created_at: datetime
    last_login: Optional[datetime] = None
    roles: List[str] = []
    scopes: List[str] = []

class UserResponse(UserBase):
    """User response model (excludes password)."""
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    roles: List[str] = []

# 2. AUTHENTICATION MODELS
class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    scopes: List[str] = []

class TokenData(BaseModel):
    """Token payload data."""
    email: Optional[str] = None
    scopes: List[str] = []

class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str

# 3. API KEY MODELS
class APIKey(BaseModel):
    """API key model."""
    key: str
    name: str
    user_id: int
    scopes: List[str] = []
    is_active: bool = True
    created_at: datetime
    expires_at: Optional[datetime] = None

class APIKeyCreate(BaseModel):
    """API key creation model."""
    name: str
    scopes: List[str] = []
    expires_days: Optional[int] = None

# MOCK DATABASES (In production, use real databases)
users_db = {
    1: UserInDB(
        id=1,
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("admin123"),
        created_at=datetime.now(),
        roles=["admin"],
        scopes=["read", "write", "admin"]
    ),
    2: UserInDB(
        id=2,
        email="user@example.com", 
        full_name="Regular User",
        hashed_password=get_password_hash("user123"),
        created_at=datetime.now(),
        roles=["user"],
        scopes=["read", "write"]
    )
}

api_keys_db = {
    "api_key_123": APIKey(
        key="api_key_123",
        name="Test API Key",
        user_id=1,
        scopes=["read", "write"],
        created_at=datetime.now()
    )
}

# Revoked tokens storage (in production, use Redis)
revoked_tokens = set()

# LINE-BY-LINE EXPLANATION OF AUTHENTICATION FUNCTIONS:

# 1. JWT TOKEN FUNCTIONS
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data (dict): Token payload data
        expires_delta (Optional[timedelta]): Token expiration time
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data (dict): Token payload data
        
    Returns:
        str: JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify JWT token.
    
    Args:
        token (str): JWT token to verify
        token_type (str): Expected token type (access or refresh)
        
    Returns:
        Optional[TokenData]: Token data if valid, None otherwise
    """
    try:
        # Check if token is revoked
        if token in revoked_tokens:
            return None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        scopes: List[str] = payload.get("scopes", [])
        token_type_claim: str = payload.get("type")
        
        if email is None or token_type_claim != token_type:
            return None
        
        return TokenData(email=email, scopes=scopes)
    except JWTError:
        return None

# 2. USER AUTHENTICATION FUNCTIONS
def get_user_by_email(email: str) -> Optional[UserInDB]:
    """
    Get user by email from database.
    
    Args:
        email (str): User email
        
    Returns:
        Optional[UserInDB]: User if found, None otherwise
    """
    for user in users_db.values():
        if user.email == email:
            return user
    return None

def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate user with email and password.
    
    Args:
        email (str): User email
        password (str): Plain text password
        
    Returns:
        Optional[UserInDB]: User if authenticated, None otherwise
    """
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# 3. API KEY AUTHENTICATION FUNCTIONS
def get_api_key_user(api_key: str) -> Optional[UserInDB]:
    """
    Get user by API key.
    
    Args:
        api_key (str): API key
        
    Returns:
        Optional[UserInDB]: User if API key is valid, None otherwise
    """
    key_data = api_keys_db.get(api_key)
    if not key_data or not key_data.is_active:
        return None
    
    # Check if API key is expired
    if key_data.expires_at and datetime.now() > key_data.expires_at:
        return None
    
    return users_db.get(key_data.user_id)

# LINE-BY-LINE EXPLANATION OF DEPENDENCY FUNCTIONS:

# 1. JWT AUTHENTICATION DEPENDENCY
def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Get current authenticated user from JWT token.
    
    This dependency extracts the JWT token from the Authorization header,
    validates it, and returns the corresponding user.
    
    Args:
        token (str): JWT token from Authorization header
        
    Returns:
        UserInDB: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Get current active user.
    
    This dependency ensures the user is active and not disabled.
    
    Args:
        current_user (UserInDB): Current user from JWT token
        
    Returns:
        UserInDB: Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# 2. API KEY AUTHENTICATION DEPENDENCY
def get_api_key_user_dependency(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInDB]:
    """
    Get user from API key authentication.
    
    This dependency checks for API key in the Authorization header
    and returns the corresponding user.
    
    Args:
        credentials (Optional[HTTPAuthorizationCredentials]): Authorization header
        
    Returns:
        Optional[UserInDB]: User if API key is valid, None otherwise
    """
    if not credentials:
        return None
    
    if credentials.scheme.lower() != "bearer":
        return None
    
    return get_api_key_user(credentials.credentials)

# 3. FLEXIBLE AUTHENTICATION DEPENDENCY
def get_current_user_flexible(
    jwt_user: Optional[UserInDB] = Depends(get_current_user),
    api_key_user: Optional[UserInDB] = Depends(get_api_key_user_dependency)
) -> UserInDB:
    """
    Get current user using either JWT or API key authentication.
    
    This dependency supports multiple authentication methods,
    checking JWT tokens first, then API keys.
    
    Args:
        jwt_user (Optional[UserInDB]): User from JWT token
        api_key_user (Optional[UserInDB]): User from API key
        
    Returns:
        UserInDB: Authenticated user
        
    Raises:
        HTTPException: If no valid authentication is provided
    """
    if jwt_user:
        return jwt_user
    
    if api_key_user:
        return api_key_user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

# 4. ROLE-BASED AUTHORIZATION
def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.
    
    This is a dependency factory that creates role-checking dependencies.
    
    Args:
        required_role (str): Required role name
        
    Returns:
        Callable: Dependency function that checks for the role
    """
    def check_role(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role"
            )
        return current_user
    
    return check_role

# 5. SCOPE-BASED AUTHORIZATION
def require_scope(required_scope: str):
    """
    Create a dependency that requires a specific scope.
    
    This is a dependency factory that creates scope-checking dependencies.
    
    Args:
        required_scope (str): Required scope name
        
    Returns:
        Callable: Dependency function that checks for the scope
    """
    def check_scope(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_scope} scope"
            )
        return current_user
    
    return check_scope

# LINE-BY-LINE EXPLANATION OF AUTHENTICATION ENDPOINTS:

# 1. USER REGISTRATION
@app.post("/auth/register", response_model=UserResponse)
def register_user(user: UserCreate):
    """
    Register a new user.
    
    This endpoint creates a new user account with hashed password.
    
    Args:
        user (UserCreate): User registration data
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If user already exists
    """
    # Check if user already exists
    if get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    new_user_id = max(users_db.keys()) + 1
    hashed_password = get_password_hash(user.password)
    
    new_user = UserInDB(
        id=new_user_id,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        created_at=datetime.now(),
        roles=["user"],
        scopes=["read", "write"]
    )
    
    users_db[new_user_id] = new_user
    
    logger.info(f"User registered: {user.email}")
    
    return UserResponse(**new_user.dict())

# 2. LOGIN WITH PASSWORD
@app.post("/auth/login", response_model=Token)
def login(login_request: LoginRequest):
    """
    Login with email and password.
    
    This endpoint authenticates a user and returns JWT tokens.
    
    Args:
        login_request (LoginRequest): Login credentials
        
    Returns:
        Token: JWT access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(login_request.email, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.now()
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scopes": user.scopes},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        scopes=user.scopes
    )

# 3. OAUTH2 TOKEN ENDPOINT
@app.post("/auth/token", response_model=Token)
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint.
    
    This endpoint provides OAuth2 Password Flow authentication.
    
    Args:
        form_data (OAuth2PasswordRequestForm): OAuth2 form data
        
    Returns:
        Token: JWT access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Filter requested scopes
    requested_scopes = form_data.scopes or []
    allowed_scopes = [scope for scope in requested_scopes if scope in user.scopes]
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scopes": allowed_scopes},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=create_refresh_token(data={"sub": user.email}),
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        scopes=allowed_scopes
    )

# 4. REFRESH TOKEN
@app.post("/auth/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.
    
    This endpoint allows clients to get a new access token
    using a valid refresh token.
    
    Args:
        refresh_token (str): Valid refresh token
        
    Returns:
        Token: New access token and refresh token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    token_data = verify_token(refresh_token, token_type="refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = get_user_by_email(token_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scopes": user.scopes},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": user.email})
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        scopes=user.scopes
    )

# 5. LOGOUT
@app.post("/auth/logout")
def logout(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Logout current user.
    
    This endpoint revokes the current user's token.
    
    Args:
        current_user (UserInDB): Current authenticated user
        
    Returns:
        dict: Logout confirmation
    """
    # In a real application, you would revoke the token
    # For now, we'll just return a success message
    
    logger.info(f"User logged out: {current_user.email}")
    
    return {"message": "Successfully logged out"}

# 6. PROTECTED ENDPOINTS WITH DIFFERENT AUTHENTICATION METHODS

@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user information.
    
    This endpoint returns information about the currently authenticated user.
    
    Args:
        current_user (UserInDB): Current authenticated user
        
    Returns:
        UserResponse: Current user information
    """
    return UserResponse(**current_user.dict())

@app.get("/auth/profile")
def get_user_profile(current_user: UserInDB = Depends(get_current_user_flexible)):
    """
    Get user profile (supports both JWT and API key auth).
    
    This endpoint demonstrates flexible authentication that accepts
    both JWT tokens and API keys.
    
    Args:
        current_user (UserInDB): Current authenticated user
        
    Returns:
        dict: User profile information
    """
    return {
        "user": UserResponse(**current_user.dict()).dict(),
        "profile_data": {
            "theme": "dark",
            "language": "en",
            "timezone": "UTC"
        }
    }

# 7. ROLE-BASED PROTECTED ENDPOINTS
@app.get("/admin/users")
def list_all_users(admin_user: UserInDB = Depends(require_role("admin"))):
    """
    List all users (admin only).
    
    This endpoint requires admin role to access.
    
    Args:
        admin_user (UserInDB): Admin user
        
    Returns:
        dict: List of all users
    """
    users = [UserResponse(**user.dict()) for user in users_db.values()]
    return {"users": users}

@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    admin_user: UserInDB = Depends(require_role("admin"))
):
    """
    Delete a user (admin only).
    
    This endpoint requires admin role to delete users.
    
    Args:
        user_id (int): User ID to delete
        admin_user (UserInDB): Admin user
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If user not found
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    deleted_user = users_db.pop(user_id)
    
    logger.info(f"User deleted by admin {admin_user.email}: {deleted_user.email}")
    
    return {"message": f"User {deleted_user.email} deleted successfully"}

# 8. SCOPE-BASED PROTECTED ENDPOINTS
@app.post("/data/create")
def create_data(
    data: dict,
    user: UserInDB = Depends(require_scope("write"))
):
    """
    Create data (requires write scope).
    
    This endpoint requires write scope to create data.
    
    Args:
        data (dict): Data to create
        user (UserInDB): User with write scope
        
    Returns:
        dict: Created data confirmation
    """
    return {
        "message": "Data created successfully",
        "data": data,
        "created_by": user.email
    }

@app.get("/data/sensitive")
def get_sensitive_data(user: UserInDB = Depends(require_scope("admin"))):
    """
    Get sensitive data (requires admin scope).
    
    This endpoint requires admin scope to access sensitive data.
    
    Args:
        user (UserInDB): User with admin scope
        
    Returns:
        dict: Sensitive data
    """
    return {
        "sensitive_data": "This is highly sensitive information",
        "accessed_by": user.email,
        "access_time": datetime.now()
    }

# 9. API KEY MANAGEMENT
@app.post("/auth/api-keys", response_model=APIKey)
def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a new API key.
    
    This endpoint allows users to create API keys for programmatic access.
    
    Args:
        api_key_data (APIKeyCreate): API key creation data
        current_user (UserInDB): Current authenticated user
        
    Returns:
        APIKey: Created API key
    """
    # Generate secure API key
    api_key = f"api_{secrets.token_urlsafe(32)}"
    
    # Set expiration if specified
    expires_at = None
    if api_key_data.expires_days:
        expires_at = datetime.now() + timedelta(days=api_key_data.expires_days)
    
    # Filter scopes to only include user's scopes
    allowed_scopes = [scope for scope in api_key_data.scopes if scope in current_user.scopes]
    
    new_api_key = APIKey(
        key=api_key,
        name=api_key_data.name,
        user_id=current_user.id,
        scopes=allowed_scopes,
        created_at=datetime.now(),
        expires_at=expires_at
    )
    
    api_keys_db[api_key] = new_api_key
    
    logger.info(f"API key created for user {current_user.email}: {api_key_data.name}")
    
    return new_api_key

@app.get("/auth/api-keys")
def list_api_keys(current_user: UserInDB = Depends(get_current_active_user)):
    """
    List user's API keys.
    
    This endpoint returns all API keys for the current user.
    
    Args:
        current_user (UserInDB): Current authenticated user
        
    Returns:
        dict: List of user's API keys
    """
    user_api_keys = [
        key for key in api_keys_db.values()
        if key.user_id == current_user.id
    ]
    
    return {"api_keys": user_api_keys}

@app.delete("/auth/api-keys/{key_id}")
def delete_api_key(
    key_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete an API key.
    
    This endpoint allows users to delete their own API keys.
    
    Args:
        key_id (str): API key to delete
        current_user (UserInDB): Current authenticated user
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If API key not found or not owned by user
    """
    if key_id not in api_keys_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key = api_keys_db[key_id]
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this API key"
        )
    
    del api_keys_db[key_id]
    
    logger.info(f"API key deleted by user {current_user.email}: {api_key.name}")
    
    return {"message": "API key deleted successfully"}

# ROOT ENDPOINT
@app.get("/")
def root():
    """Root endpoint with authentication examples."""
    return {
        "message": "FastAPI Authentication & Security Tutorial",
        "authentication_methods": {
            "jwt_tokens": "Bearer tokens for web applications",
            "api_keys": "API keys for programmatic access",
            "oauth2": "OAuth2 Password Flow for standard clients"
        },
        "endpoints": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "oauth2_token": "POST /auth/token",
            "refresh": "POST /auth/refresh",
            "logout": "POST /auth/logout",
            "profile": "GET /auth/me",
            "admin_users": "GET /admin/users (admin only)",
            "create_data": "POST /data/create (write scope)",
            "sensitive_data": "GET /data/sensitive (admin scope)",
            "api_keys": "POST /auth/api-keys"
        },
        "test_accounts": {
            "admin": {"email": "admin@example.com", "password": "admin123"},
            "user": {"email": "user@example.com", "password": "user123"}
        },
        "security_features": {
            "password_hashing": "bcrypt for secure password storage",
            "jwt_tokens": "JSON Web Tokens for stateless authentication",
            "token_refresh": "Refresh tokens for extended sessions",
            "role_based_access": "Role-based authorization",
            "scope_based_access": "Scope-based fine-grained permissions",
            "api_key_auth": "API keys for programmatic access",
            "cors_protection": "CORS middleware for web security"
        }
    }

# WHAT YOU'VE LEARNED:
"""
1. Authentication Methods:
   - JWT tokens for web applications
   - API keys for programmatic access
   - OAuth2 Password Flow for standard clients
   - Flexible authentication supporting multiple methods

2. Security Features:
   - Password hashing with bcrypt
   - Secure token generation and validation
   - Token refresh mechanism
   - Token revocation (logout)
   - CORS protection

3. Authorization Patterns:
   - Role-based access control (RBAC)
   - Scope-based permissions
   - Dependency injection for auth checks
   - Flexible authorization requirements

4. Security Best Practices:
   - Never store plain passwords
   - Use secure random tokens
   - Implement proper token expiration
   - Log security events
   - Validate all inputs
   - Use HTTPS in production

5. Production Considerations:
   - Store secrets in environment variables
   - Use Redis for token blacklisting
   - Implement rate limiting
   - Add monitoring and alerting
   - Regular security audits
   - Keep dependencies updated

6. Advanced Features:
   - Multiple authentication methods
   - API key management
   - Granular permissions
   - Audit logging
   - Token introspection
   - Custom authentication flows

NEXT: Move to 10_database_integration.py to learn about database operations!
""" 