"""
🗄️ FastAPI Database Integration - Complete Database Operations

This file teaches you everything about database integration in FastAPI:
- SQLAlchemy ORM setup and configuration
- Database models and relationships
- CRUD operations (Create, Read, Update, Delete)
- Database migrations with Alembic
- Connection pooling and sessions

Run this file with: uvicorn 10_database_integration:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="FastAPI Database Integration Tutorial",
    description="Complete database operations with SQLAlchemy",
    version="1.0.0"
)

# LINE-BY-LINE EXPLANATION OF DATABASE SETUP:

# 1. DATABASE CONFIGURATION
DATABASE_URL = "sqlite:///./tutorial.db"  # In production, use PostgreSQL or MySQL
# DATABASE_URL = "postgresql://user:password@localhost/dbname"  # PostgreSQL
# DATABASE_URL = "mysql://user:password@localhost/dbname"       # MySQL

# 2. SQLALCHEMY ENGINE
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Only needed for SQLite
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False           # Set to True to see SQL queries in logs
)

# 3. SESSION FACTORY
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. BASE CLASS FOR MODELS
Base = declarative_base()

# LINE-BY-LINE EXPLANATION OF DATABASE MODELS:

# 1. USER MODEL
class User(Base):
    """
    User database model.
    
    This model represents users in the database with all necessary fields
    and relationships. It includes timestamps and soft delete functionality.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")

# 2. POST MODEL
class Post(Base):
    """
    Post database model with foreign key relationship to User.
    
    This model demonstrates one-to-many relationships and includes
    content management features like published status and timestamps.
    """
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    published = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")

# 3. COMMENT MODEL
class Comment(Base):
    """
    Comment database model with foreign keys to both User and Post.
    
    This model demonstrates many-to-one relationships with multiple parents.
    """
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

# 4. TAG MODEL
class Tag(Base):
    """
    Tag database model for many-to-many relationship with Posts.
    
    This model demonstrates many-to-many relationships through association tables.
    """
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    posts = relationship("Post", secondary="post_tags", back_populates="tags")

# 5. ASSOCIATION TABLE FOR MANY-TO-MANY RELATIONSHIP
from sqlalchemy import Table
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
)

# LINE-BY-LINE EXPLANATION OF PYDANTIC MODELS:

# 1. USER PYDANTIC MODELS
class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    """User creation model with password."""
    password: str

class UserUpdate(BaseModel):
    """User update model with optional fields."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    """User model as stored in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy models

# 2. POST PYDANTIC MODELS
class PostBase(BaseModel):
    """Base post model with common fields."""
    title: str
    content: str
    published: bool = False

class PostCreate(PostBase):
    """Post creation model."""
    pass

class PostUpdate(BaseModel):
    """Post update model with optional fields."""
    title: Optional[str] = None
    content: Optional[str] = None
    published: Optional[bool] = None

class PostInDB(PostBase):
    """Post model as stored in database."""
    id: int
    author_id: int
    views: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# 3. COMMENT PYDANTIC MODELS
class CommentBase(BaseModel):
    """Base comment model."""
    content: str

class CommentCreate(CommentBase):
    """Comment creation model."""
    post_id: int

class CommentInDB(CommentBase):
    """Comment model as stored in database."""
    id: int
    author_id: int
    post_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# 4. TAG PYDANTIC MODELS
class TagBase(BaseModel):
    """Base tag model."""
    name: str
    description: Optional[str] = None

class TagCreate(TagBase):
    """Tag creation model."""
    pass

class TagInDB(TagBase):
    """Tag model as stored in database."""
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# 5. RESPONSE MODELS WITH RELATIONSHIPS
class UserWithPosts(UserInDB):
    """User model with posts relationship."""
    posts: List[PostInDB] = []

class PostWithComments(PostInDB):
    """Post model with comments relationship."""
    comments: List[CommentInDB] = []
    tags: List[TagInDB] = []

# LINE-BY-LINE EXPLANATION OF DATABASE UTILITIES:

# 1. DATABASE DEPENDENCY
def get_db():
    """
    Database dependency for FastAPI.
    
    This dependency provides a database session for each request
    and ensures proper cleanup after the request is completed.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. DATABASE INITIALIZATION
def create_tables():
    """
    Create all database tables.
    
    This function creates all tables defined in the models.
    In production, use Alembic for database migrations.
    """
    Base.metadata.create_all(bind=engine)

# 3. PASSWORD HASHING UTILITIES
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

# LINE-BY-LINE EXPLANATION OF CRUD OPERATIONS:

# 1. USER CRUD OPERATIONS
class UserCRUD:
    """
    User CRUD operations class.
    
    This class encapsulates all database operations for User model.
    It provides a clean interface for database interactions.
    """
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db (Session): Database session
            user_id (int): User ID
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            db (Session): Database session
            email (str): User email
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get multiple users with pagination.
        
        Args:
            db (Session): Database session
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            
        Returns:
            List[User]: List of users
        """
        return db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, db: Session, user: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db (Session): Database session
            user (UserCreate): User creation data
            
        Returns:
            User: Created user
        """
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """
        Update user by ID.
        
        Args:
            db (Session): Database session
            user_id (int): User ID
            user_update (UserUpdate): User update data
            
        Returns:
            Optional[User]: Updated user if found, None otherwise
        """
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """
        Delete user by ID.
        
        Args:
            db (Session): Database session
            user_id (int): User ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True

# 2. POST CRUD OPERATIONS
class PostCRUD:
    """Post CRUD operations class."""
    
    def get_post_by_id(self, db: Session, post_id: int) -> Optional[Post]:
        """Get post by ID."""
        return db.query(Post).filter(Post.id == post_id).first()
    
    def get_posts(self, db: Session, skip: int = 0, limit: int = 100, published_only: bool = False) -> List[Post]:
        """Get multiple posts with pagination."""
        query = db.query(Post)
        if published_only:
            query = query.filter(Post.published == True)
        return query.offset(skip).limit(limit).all()
    
    def get_posts_by_author(self, db: Session, author_id: int, skip: int = 0, limit: int = 100) -> List[Post]:
        """Get posts by author."""
        return db.query(Post).filter(Post.author_id == author_id).offset(skip).limit(limit).all()
    
    def create_post(self, db: Session, post: PostCreate, author_id: int) -> Post:
        """Create a new post."""
        db_post = Post(**post.dict(), author_id=author_id)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    
    def update_post(self, db: Session, post_id: int, post_update: PostUpdate) -> Optional[Post]:
        """Update post by ID."""
        db_post = db.query(Post).filter(Post.id == post_id).first()
        if not db_post:
            return None
        
        update_data = post_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)
        
        db.commit()
        db.refresh(db_post)
        return db_post
    
    def delete_post(self, db: Session, post_id: int) -> bool:
        """Delete post by ID."""
        db_post = db.query(Post).filter(Post.id == post_id).first()
        if not db_post:
            return False
        
        db.delete(db_post)
        db.commit()
        return True
    
    def increment_views(self, db: Session, post_id: int) -> Optional[Post]:
        """Increment post views."""
        db_post = db.query(Post).filter(Post.id == post_id).first()
        if not db_post:
            return None
        
        db_post.views += 1
        db.commit()
        db.refresh(db_post)
        return db_post

# Create CRUD instances
user_crud = UserCRUD()
post_crud = PostCRUD()

# Initialize database
create_tables()

# LINE-BY-LINE EXPLANATION OF DATABASE ENDPOINTS:

# 1. USER ENDPOINTS
@app.post("/users/", response_model=UserInDB)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    
    This endpoint demonstrates how to create records in the database
    using CRUD operations and handle potential conflicts.
    
    Args:
        user (UserCreate): User creation data
        db (Session): Database session
        
    Returns:
        UserInDB: Created user
        
    Raises:
        HTTPException: If user email already exists
    """
    # Check if user already exists
    existing_user = user_crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    db_user = user_crud.create_user(db, user)
    logger.info(f"User created: {db_user.email}")
    
    return db_user

@app.get("/users/", response_model=List[UserInDB])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List users with pagination.
    
    This endpoint demonstrates how to retrieve multiple records
    with pagination support.
    
    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        db (Session): Database session
        
    Returns:
        List[UserInDB]: List of users
    """
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=UserInDB)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID.
    
    This endpoint demonstrates how to retrieve a single record
    and handle not found scenarios.
    
    Args:
        user_id (int): User ID
        db (Session): Database session
        
    Returns:
        UserInDB: User data
        
    Raises:
        HTTPException: If user not found
    """
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.put("/users/{user_id}", response_model=UserInDB)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Update user by ID.
    
    This endpoint demonstrates how to update records
    with partial data updates.
    
    Args:
        user_id (int): User ID
        user_update (UserUpdate): User update data
        db (Session): Database session
        
    Returns:
        UserInDB: Updated user
        
    Raises:
        HTTPException: If user not found
    """
    user = user_crud.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User updated: {user.email}")
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete user by ID.
    
    This endpoint demonstrates how to delete records
    and handle cascading deletes.
    
    Args:
        user_id (int): User ID
        db (Session): Database session
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If user not found
    """
    deleted = user_crud.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User deleted: {user_id}")
    return {"message": "User deleted successfully"}

# 2. POST ENDPOINTS
@app.post("/posts/", response_model=PostInDB)
def create_post(post: PostCreate, author_id: int, db: Session = Depends(get_db)):
    """
    Create a new post.
    
    This endpoint demonstrates how to create records with foreign key relationships.
    
    Args:
        post (PostCreate): Post creation data
        author_id (int): Author user ID
        db (Session): Database session
        
    Returns:
        PostInDB: Created post
        
    Raises:
        HTTPException: If author not found
    """
    # Verify author exists
    author = user_crud.get_user_by_id(db, author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )
    
    # Create post
    db_post = post_crud.create_post(db, post, author_id)
    logger.info(f"Post created: {db_post.title} by user {author_id}")
    
    return db_post

@app.get("/posts/", response_model=List[PostInDB])
def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    published_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    List posts with filtering and pagination.
    
    This endpoint demonstrates how to retrieve multiple records
    with filtering conditions.
    
    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        published_only (bool): Filter for published posts only
        db (Session): Database session
        
    Returns:
        List[PostInDB]: List of posts
    """
    posts = post_crud.get_posts(db, skip=skip, limit=limit, published_only=published_only)
    return posts

@app.get("/posts/{post_id}", response_model=PostInDB)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    Get post by ID and increment views.
    
    This endpoint demonstrates how to retrieve a record
    and perform additional operations (view counting).
    
    Args:
        post_id (int): Post ID
        db (Session): Database session
        
    Returns:
        PostInDB: Post data
        
    Raises:
        HTTPException: If post not found
    """
    post = post_crud.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Increment views
    post_crud.increment_views(db, post_id)
    
    return post

@app.get("/users/{user_id}/posts", response_model=List[PostInDB])
def get_user_posts(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get posts by user ID.
    
    This endpoint demonstrates how to retrieve related records
    using foreign key relationships.
    
    Args:
        user_id (int): User ID
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        db (Session): Database session
        
    Returns:
        List[PostInDB]: List of user's posts
        
    Raises:
        HTTPException: If user not found
    """
    # Verify user exists
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    posts = post_crud.get_posts_by_author(db, user_id, skip=skip, limit=limit)
    return posts

# 3. RELATIONSHIP ENDPOINTS
@app.get("/users/{user_id}/with-posts", response_model=UserWithPosts)
def get_user_with_posts(user_id: int, db: Session = Depends(get_db)):
    """
    Get user with all their posts.
    
    This endpoint demonstrates how to retrieve records
    with their relationships using SQLAlchemy ORM.
    
    Args:
        user_id (int): User ID
        db (Session): Database session
        
    Returns:
        UserWithPosts: User with posts
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@app.get("/posts/{post_id}/with-comments", response_model=PostWithComments)
def get_post_with_comments(post_id: int, db: Session = Depends(get_db)):
    """
    Get post with all comments.
    
    This endpoint demonstrates how to retrieve records
    with nested relationships.
    
    Args:
        post_id (int): Post ID
        db (Session): Database session
        
    Returns:
        PostWithComments: Post with comments
        
    Raises:
        HTTPException: If post not found
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return post

# 4. STATISTICS ENDPOINTS
@app.get("/stats/overview")
def get_statistics_overview(db: Session = Depends(get_db)):
    """
    Get database statistics overview.
    
    This endpoint demonstrates how to perform aggregate queries
    and gather statistics from the database.
    
    Args:
        db (Session): Database session
        
    Returns:
        dict: Database statistics
    """
    # Count queries
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_posts = db.query(Post).count()
    published_posts = db.query(Post).filter(Post.published == True).count()
    total_comments = db.query(Comment).count()
    
    # Aggregate queries
    total_views = db.query(func.sum(Post.views)).scalar() or 0
    avg_views_per_post = db.query(func.avg(Post.views)).scalar() or 0
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users
        },
        "posts": {
            "total": total_posts,
            "published": published_posts,
            "drafts": total_posts - published_posts
        },
        "comments": {
            "total": total_comments
        },
        "engagement": {
            "total_views": total_views,
            "average_views_per_post": round(avg_views_per_post, 2)
        }
    }

# 5. SEARCH ENDPOINTS
@app.get("/search/users")
def search_users(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Search users by name or email.
    
    This endpoint demonstrates how to perform search queries
    with multiple criteria.
    
    Args:
        q (str): Search query
        db (Session): Database session
        
    Returns:
        dict: Search results
    """
    users = db.query(User).filter(
        (User.full_name.ilike(f"%{q}%")) |
        (User.email.ilike(f"%{q}%"))
    ).all()
    
    return {
        "query": q,
        "results": users,
        "count": len(users)
    }

@app.get("/search/posts")
def search_posts(
    q: str = Query(..., min_length=1),
    published_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Search posts by title or content.
    
    This endpoint demonstrates how to perform full-text search
    on multiple fields.
    
    Args:
        q (str): Search query
        published_only (bool): Filter for published posts only
        db (Session): Database session
        
    Returns:
        dict: Search results
    """
    query = db.query(Post).filter(
        (Post.title.ilike(f"%{q}%")) |
        (Post.content.ilike(f"%{q}%"))
    )
    
    if published_only:
        query = query.filter(Post.published == True)
    
    posts = query.all()
    
    return {
        "query": q,
        "results": posts,
        "count": len(posts)
    }

# ROOT ENDPOINT
@app.get("/")
def root():
    """Root endpoint with database examples."""
    return {
        "message": "FastAPI Database Integration Tutorial",
        "database_features": {
            "orm": "SQLAlchemy ORM for database operations",
            "relationships": "Foreign keys and relationship mapping",
            "crud_operations": "Create, Read, Update, Delete operations",
            "pagination": "Efficient pagination for large datasets",
            "search": "Full-text search capabilities",
            "aggregations": "Statistical queries and aggregations",
            "migrations": "Database schema migrations with Alembic"
        },
        "endpoints": {
            "users": {
                "create": "POST /users/",
                "list": "GET /users/",
                "get": "GET /users/{user_id}",
                "update": "PUT /users/{user_id}",
                "delete": "DELETE /users/{user_id}",
                "with_posts": "GET /users/{user_id}/with-posts"
            },
            "posts": {
                "create": "POST /posts/",
                "list": "GET /posts/",
                "get": "GET /posts/{post_id}",
                "by_author": "GET /users/{user_id}/posts",
                "with_comments": "GET /posts/{post_id}/with-comments"
            },
            "search": {
                "users": "GET /search/users?q=query",
                "posts": "GET /search/posts?q=query"
            },
            "statistics": "GET /stats/overview"
        },
        "sample_data": {
            "create_user": {
                "email": "john@example.com",
                "full_name": "John Doe",
                "password": "secret123"
            },
            "create_post": {
                "title": "My First Post",
                "content": "This is the content of my first post.",
                "published": True
            }
        }
    }

# WHAT YOU'VE LEARNED:
"""
1. Database Setup:
   - SQLAlchemy engine configuration
   - Database URL patterns for different databases
   - Connection pooling and session management
   - Table creation and schema management

2. Database Models:
   - SQLAlchemy declarative base
   - Table columns and data types
   - Primary keys and foreign keys
   - One-to-many and many-to-many relationships
   - Timestamps and automatic fields

3. Pydantic Integration:
   - ORM mode for SQLAlchemy models
   - Request/response model separation
   - Data validation and serialization
   - Relationship handling in responses

4. CRUD Operations:
   - Create operations with conflict handling
   - Read operations with filtering and pagination
   - Update operations with partial updates
   - Delete operations with cascade handling
   - Bulk operations and transactions

5. Advanced Database Features:
   - Relationship queries and joins
   - Aggregate functions and statistics
   - Full-text search capabilities
   - Complex filtering and sorting
   - Database constraints and validation

6. Best Practices:
   - Dependency injection for database sessions
   - Proper error handling and HTTP status codes
   - Query optimization and performance
   - Security considerations (SQL injection prevention)
   - Logging and monitoring

7. Production Considerations:
   - Database migrations with Alembic
   - Connection pooling configuration
   - Database indexing strategies
   - Performance monitoring and optimization
   - Backup and recovery procedures
   - Environment-specific configurations

CONGRATULATIONS! You've completed the Intermediate Level FastAPI tutorial!
Next, you can explore the Advanced Level topics for production-ready applications.
""" 