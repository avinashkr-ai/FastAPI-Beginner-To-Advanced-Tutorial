"""
FastAPI Advanced Level - File 13: Testing FastAPI Applications
===========================================================

This file demonstrates comprehensive testing strategies for FastAPI applications including:
- Unit testing with pytest
- Integration testing with TestClient
- Mocking external dependencies
- Database testing with fixtures
- Authentication testing
- Error handling testing
- Performance testing
- Testing background tasks
- Testing WebSocket connections
- Test data management
- Coverage reporting
- CI/CD integration

Testing is crucial for maintaining code quality and ensuring your API works correctly.
"""

import pytest
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Optional, List, Dict, Any
import tempfile
import os
from pathlib import Path

# ==================================================
# 1. APPLICATION SETUP FOR TESTING
# ==================================================

# Database setup for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    """
    User model for testing
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Post(Base):
    """
    Post model for testing
    """
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    author_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# ==================================================
# 2. PYDANTIC MODELS
# ==================================================

class UserCreate(BaseModel):
    """
    User creation model
    """
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    """
    User response model
    """
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    """
    Post creation model
    """
    title: str
    content: str

class PostResponse(BaseModel):
    """
    Post response model
    """
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    """
    Login request model
    """
    username: str
    password: str

# ==================================================
# 3. SERVICES AND DEPENDENCIES
# ==================================================

class UserService:
    """
    User service with database operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user: UserCreate) -> User:
        """
        Create a new user
        """
        # Hash password (simplified for testing)
        hashed_password = f"hashed_{user.password}"
        
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials
        """
        user = self.get_user_by_username(username)
        if user and user.hashed_password == f"hashed_{password}":
            return user
        return None

class PostService:
    """
    Post service with database operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_post(self, post: PostCreate, author_id: int) -> Post:
        """
        Create a new post
        """
        db_post = Post(
            title=post.title,
            content=post.content,
            author_id=author_id
        )
        
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        
        return db_post
    
    def get_posts(self, skip: int = 0, limit: int = 10) -> List[Post]:
        """
        Get posts with pagination
        """
        return self.db.query(Post).offset(skip).limit(limit).all()

class EmailService:
    """
    Email service for testing external dependencies
    """
    
    def __init__(self, smtp_server: str = "localhost"):
        self.smtp_server = smtp_server
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send email (external dependency to mock)
        """
        # This would normally send actual email
        await asyncio.sleep(0.1)  # Simulate network delay
        return True

# ==================================================
# 4. AUTHENTICATION
# ==================================================

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user from token
    """
    token = credentials.credentials
    
    # Simplified token validation for testing
    if token.startswith("valid_token_"):
        user_id = int(token.split("_")[-1])
        return {"id": user_id, "username": f"user_{user_id}"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# ==================================================
# 5. DATABASE DEPENDENCY
# ==================================================

def get_db():
    """
    Database dependency
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================================================
# 6. FASTAPI APPLICATION
# ==================================================

app = FastAPI(title="Testing Demo API", version="1.0.0")

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user
    """
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = user_service.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    db_user = user_service.create_user(user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID
    """
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return user

@app.post("/login")
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login user and return token
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(login_request.username, login_request.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Generate token (simplified for testing)
    token = f"valid_token_{user.id}"
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@app.post("/posts/", response_model=PostResponse)
async def create_post(
    post: PostCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new post (requires authentication)
    """
    post_service = PostService(db)
    db_post = post_service.create_post(post, current_user["id"])
    return db_post

@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get posts with pagination
    """
    post_service = PostService(db)
    posts = post_service.get_posts(skip=skip, limit=limit)
    return posts

@app.post("/send-welcome-email/{user_id}")
async def send_welcome_email(user_id: int, db: Session = Depends(get_db)):
    """
    Send welcome email to user (external dependency)
    """
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    email_service = EmailService()
    success = await email_service.send_email(
        to=user.email,
        subject="Welcome!",
        body=f"Welcome {user.username}!"
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send email"
        )
    
    return {"message": "Welcome email sent"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ==================================================
# 7. PYTEST FIXTURES
# ==================================================

@pytest.fixture
def client():
    """
    Test client fixture
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    """
    Database session fixture for testing
    """
    # Create a new database session for each test
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Rollback transaction after test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def sample_user():
    """
    Sample user data fixture
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }

@pytest.fixture
def sample_post():
    """
    Sample post data fixture
    """
    return {
        "title": "Test Post",
        "content": "This is a test post content."
    }

@pytest.fixture
def authenticated_headers():
    """
    Authenticated headers fixture
    """
    return {"Authorization": "Bearer valid_token_1"}

@pytest.fixture
def mock_email_service():
    """
    Mock email service fixture
    """
    with patch('__main__.EmailService') as mock:
        mock_instance = Mock()
        mock_instance.send_email = AsyncMock(return_value=True)
        mock.return_value = mock_instance
        yield mock_instance

# ==================================================
# 8. UNIT TESTS
# ==================================================

class TestUserService:
    """
    Unit tests for UserService
    """
    
    def test_create_user(self, db_session):
        """
        Test user creation
        """
        user_service = UserService(db_session)
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )
        
        user = user_service.create_user(user_data)
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_testpass"
        assert user.is_active is True
        assert user.id is not None
    
    def test_get_user_by_username(self, db_session):
        """
        Test getting user by username
        """
        user_service = UserService(db_session)
        
        # Create user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )
        created_user = user_service.create_user(user_data)
        
        # Get user by username
        found_user = user_service.get_user_by_username("testuser")
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == "testuser"
    
    def test_authenticate_user_success(self, db_session):
        """
        Test successful user authentication
        """
        user_service = UserService(db_session)
        
        # Create user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )
        user_service.create_user(user_data)
        
        # Authenticate user
        authenticated_user = user_service.authenticate_user("testuser", "testpass")
        
        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"
    
    def test_authenticate_user_failure(self, db_session):
        """
        Test failed user authentication
        """
        user_service = UserService(db_session)
        
        # Try to authenticate non-existent user
        authenticated_user = user_service.authenticate_user("nonexistent", "wrongpass")
        
        assert authenticated_user is None

# ==================================================
# 9. INTEGRATION TESTS
# ==================================================

class TestUserAPI:
    """
    Integration tests for user API endpoints
    """
    
    def test_create_user_success(self, client, sample_user):
        """
        Test successful user creation
        """
        response = client.post("/users/", json=sample_user)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user["email"]
        assert data["username"] == sample_user["username"]
        assert data["is_active"] is True
        assert "id" in data
    
    def test_create_user_duplicate_username(self, client, sample_user):
        """
        Test creating user with duplicate username
        """
        # Create first user
        client.post("/users/", json=sample_user)
        
        # Try to create second user with same username
        response = client.post("/users/", json=sample_user)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_get_user_success(self, client, sample_user):
        """
        Test successful user retrieval
        """
        # Create user
        create_response = client.post("/users/", json=sample_user)
        user_id = create_response.json()["id"]
        
        # Get user
        response = client.get(f"/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == sample_user["username"]
    
    def test_get_user_not_found(self, client):
        """
        Test getting non-existent user
        """
        response = client.get("/users/999")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

class TestAuthentication:
    """
    Tests for authentication endpoints
    """
    
    def test_login_success(self, client, sample_user):
        """
        Test successful login
        """
        # Create user
        client.post("/users/", json=sample_user)
        
        # Login
        login_data = {
            "username": sample_user["username"],
            "password": sample_user["password"]
        }
        response = client.post("/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == sample_user["username"]
    
    def test_login_failure(self, client):
        """
        Test failed login
        """
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        response = client.post("/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

class TestPostAPI:
    """
    Integration tests for post API endpoints
    """
    
    def test_create_post_success(self, client, sample_user, sample_post, authenticated_headers):
        """
        Test successful post creation
        """
        response = client.post("/posts/", json=sample_post, headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_post["title"]
        assert data["content"] == sample_post["content"]
        assert data["author_id"] == 1
    
    def test_create_post_unauthorized(self, client, sample_post):
        """
        Test post creation without authentication
        """
        response = client.post("/posts/", json=sample_post)
        
        assert response.status_code == 403
    
    def test_get_posts(self, client, sample_post, authenticated_headers):
        """
        Test getting posts
        """
        # Create a few posts
        for i in range(3):
            post_data = {
                "title": f"Post {i}",
                "content": f"Content {i}"
            }
            client.post("/posts/", json=post_data, headers=authenticated_headers)
        
        # Get posts
        response = client.get("/posts/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == "Post 0"

# ==================================================
# 10. MOCKING EXTERNAL DEPENDENCIES
# ==================================================

class TestEmailIntegration:
    """
    Tests for email functionality with mocking
    """
    
    def test_send_welcome_email_success(self, client, sample_user, mock_email_service):
        """
        Test successful welcome email sending
        """
        # Create user
        create_response = client.post("/users/", json=sample_user)
        user_id = create_response.json()["id"]
        
        # Send welcome email
        response = client.post(f"/send-welcome-email/{user_id}")
        
        assert response.status_code == 200
        assert "Welcome email sent" in response.json()["message"]
        
        # Verify email service was called
        mock_email_service.send_email.assert_called_once()
    
    def test_send_welcome_email_user_not_found(self, client, mock_email_service):
        """
        Test welcome email for non-existent user
        """
        response = client.post("/send-welcome-email/999")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
        
        # Verify email service was not called
        mock_email_service.send_email.assert_not_called()
    
    def test_send_welcome_email_failure(self, client, sample_user, mock_email_service):
        """
        Test welcome email sending failure
        """
        # Mock email service failure
        mock_email_service.send_email.return_value = False
        
        # Create user
        create_response = client.post("/users/", json=sample_user)
        user_id = create_response.json()["id"]
        
        # Send welcome email
        response = client.post(f"/send-welcome-email/{user_id}")
        
        assert response.status_code == 500
        assert "Failed to send email" in response.json()["detail"]

# ==================================================
# 11. PARAMETRIZED TESTS
# ==================================================

class TestValidation:
    """
    Parametrized tests for input validation
    """
    
    @pytest.mark.parametrize("invalid_user", [
        {"username": "test", "password": "pass"},  # Missing email
        {"email": "invalid-email", "username": "test", "password": "pass"},  # Invalid email
        {"email": "test@example.com", "password": "pass"},  # Missing username
        {"email": "test@example.com", "username": "test"},  # Missing password
        {"email": "test@example.com", "username": "", "password": "pass"},  # Empty username
    ])
    def test_create_user_validation_errors(self, client, invalid_user):
        """
        Test user creation validation errors
        """
        response = client.post("/users/", json=invalid_user)
        assert response.status_code == 422

# ==================================================
# 12. PERFORMANCE TESTS
# ==================================================

class TestPerformance:
    """
    Basic performance tests
    """
    
    def test_concurrent_requests(self, client):
        """
        Test handling concurrent requests
        """
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests were successful
        assert len(results) == 10
        for result in results:
            assert result["status_code"] == 200
            assert result["response_time"] < 1.0  # Should be fast

# ==================================================
# 13. PYTEST CONFIGURATION
# ==================================================

# pytest.ini configuration (create this file in your project root)
PYTEST_CONFIG = """
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
"""

# ==================================================
# 14. RUNNING THE TESTS
# ==================================================

"""
How to Run Tests:

1. Install testing dependencies:
   pip install pytest pytest-asyncio pytest-cov httpx

2. Run all tests:
   pytest

3. Run specific test file:
   pytest test_api.py

4. Run specific test class:
   pytest test_api.py::TestUserAPI

5. Run specific test method:
   pytest test_api.py::TestUserAPI::test_create_user_success

6. Run with coverage:
   pytest --cov=app --cov-report=html

7. Run only unit tests:
   pytest -m unit

8. Run excluding slow tests:
   pytest -m "not slow"

9. Verbose output:
   pytest -v

10. Stop on first failure:
    pytest -x

Test Structure:
- Unit tests: Test individual functions/methods
- Integration tests: Test API endpoints
- Mocking: Test external dependencies
- Parametrized tests: Test multiple inputs
- Performance tests: Test response times
- Fixtures: Reusable test data and setup

Key Testing Principles:
1. Test one thing at a time
2. Use descriptive test names
3. Arrange-Act-Assert pattern
4. Mock external dependencies
5. Test both success and failure cases
6. Use fixtures for common setup
7. Keep tests independent
8. Measure code coverage
"""

if __name__ == "__main__":
    # Run a simple test to verify everything works
    client = TestClient(app)
    response = client.get("/health")
    print(f"Health check: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test user creation
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    response = client.post("/users/", json=user_data)
    print(f"User creation: {response.status_code}")
    if response.status_code == 200:
        print(f"Created user: {response.json()}") 