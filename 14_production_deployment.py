"""
FastAPI Advanced Level - File 14: Production Deployment
====================================================

This file covers production deployment strategies for FastAPI applications including:
- Docker containerization
- Environment configuration
- Health checks and monitoring
- Security best practices
- Performance optimization
- Load balancing
- CI/CD integration
- Logging and observability
- Database migrations
- Scaling strategies
- Error tracking
- Backup and recovery

Production deployment requires careful consideration of security, performance, and reliability.
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import psutil
import time
from pathlib import Path
import json
from contextlib import asynccontextmanager

# ==================================================
# 1. ENVIRONMENT CONFIGURATION
# ==================================================

class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    
    # Application settings
    app_name: str = Field(default="FastAPI Production App", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="production", description="Environment (development/staging/production)")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")
    
    # Database settings
    database_url: str = Field(default="postgresql://user:password@localhost/dbname", description="Database URL")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections")
    
    # Security settings
    secret_key: str = Field(default="your-secret-key-change-in-production", description="Secret key for JWT")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], description="Allowed hosts")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    # Redis settings (for caching and sessions)
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Log level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Performance settings
    max_connections: int = Field(default=1000, description="Maximum number of connections")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # Email settings
    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    
    # Storage settings
    upload_dir: str = Field(default="uploads", description="Upload directory")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes")
    
    # Backup settings
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_schedule: str = Field(default="0 2 * * *", description="Backup schedule (cron format)")
    backup_retention_days: int = Field(default=30, description="Backup retention in days")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# ==================================================
# 2. LOGGING CONFIGURATION
# ==================================================

def setup_logging():
    """
    Configure logging for production
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(settings.log_file) if settings.log_file else logging.NullHandler()
        ]
    )
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Create logger for this application
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {settings.environment} environment")
    
    return logger

logger = setup_logging()

# ==================================================
# 3. HEALTH CHECK MODELS
# ==================================================

class HealthStatus(BaseModel):
    """
    Health check status model
    """
    status: str = Field(description="Overall health status")
    timestamp: datetime = Field(description="Check timestamp")
    version: str = Field(description="Application version")
    environment: str = Field(description="Environment name")
    uptime: float = Field(description="Uptime in seconds")
    checks: Dict[str, Any] = Field(description="Individual health checks")

class SystemMetrics(BaseModel):
    """
    System metrics model
    """
    cpu_usage: float = Field(description="CPU usage percentage")
    memory_usage: float = Field(description="Memory usage percentage")
    disk_usage: float = Field(description="Disk usage percentage")
    network_io: Dict[str, int] = Field(description="Network I/O statistics")
    process_count: int = Field(description="Number of processes")
    open_files: int = Field(description="Number of open files")

# ==================================================
# 4. HEALTH CHECK SERVICES
# ==================================================

class HealthChecker:
    """
    Comprehensive health check service
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = {}
    
    async def check_database(self) -> Dict[str, Any]:
        """
        Check database connectivity
        """
        try:
            # Simulate database check
            await asyncio.sleep(0.1)
            return {
                "status": "healthy",
                "response_time": 0.1,
                "connections": {
                    "active": 5,
                    "idle": 3,
                    "total": 8
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """
        Check Redis connectivity
        """
        try:
            # Simulate Redis check
            await asyncio.sleep(0.05)
            return {
                "status": "healthy",
                "response_time": 0.05,
                "memory_usage": "10MB",
                "connected_clients": 2
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_external_services(self) -> Dict[str, Any]:
        """
        Check external service dependencies
        """
        try:
            # Simulate external service check
            await asyncio.sleep(0.2)
            return {
                "status": "healthy",
                "services": {
                    "payment_gateway": "healthy",
                    "email_service": "healthy",
                    "cdn": "healthy"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Get system performance metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Process information
            process = psutil.Process()
            process_count = len(psutil.pids())
            open_files = len(process.open_files())
            
            return SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                disk_usage=disk_percent,
                network_io=network_io,
                process_count=process_count,
                open_files=open_files
            )
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                process_count=0,
                open_files=0
            )
    
    async def perform_health_check(self) -> HealthStatus:
        """
        Perform comprehensive health check
        """
        checks = {}
        overall_status = "healthy"
        
        # Check database
        db_check = await self.check_database()
        checks["database"] = db_check
        if db_check["status"] != "healthy":
            overall_status = "unhealthy"
        
        # Check Redis
        redis_check = await self.check_redis()
        checks["redis"] = redis_check
        if redis_check["status"] != "healthy":
            overall_status = "degraded"
        
        # Check external services
        external_check = await self.check_external_services()
        checks["external_services"] = external_check
        if external_check["status"] != "healthy":
            overall_status = "degraded"
        
        # System metrics
        metrics = self.get_system_metrics()
        checks["system_metrics"] = metrics.dict()
        
        # Check system thresholds
        if metrics.cpu_usage > 90 or metrics.memory_usage > 90:
            overall_status = "degraded"
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            environment=settings.environment,
            uptime=time.time() - self.start_time,
            checks=checks
        )

# ==================================================
# 5. MIDDLEWARE FOR PRODUCTION
# ==================================================

class SecurityMiddleware:
    """
    Security middleware for production
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
        
        # Add security headers middleware
        @app.middleware("http")
        async def security_headers(request: Request, call_next):
            response = await call_next(request)
            
            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Remove server header
            response.headers.pop("Server", None)
            
            return response
        
        # Add request logging middleware
        @app.middleware("http")
        async def request_logging(request: Request, call_next):
            start_time = time.time()
            
            # Log request
            logger.info(f"Request: {request.method} {request.url}")
            
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
            
            return response

# ==================================================
# 6. APPLICATION SETUP
# ==================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    """
    logger.info(f"Starting {settings.app_name} in {settings.environment} environment")
    
    # Startup tasks
    await startup_tasks()
    
    yield
    
    # Shutdown tasks
    await shutdown_tasks()
    
    logger.info("Application shutdown complete")

async def startup_tasks():
    """
    Tasks to run on application startup
    """
    logger.info("Running startup tasks...")
    
    # Initialize database connections
    logger.info("Initializing database connections...")
    
    # Initialize Redis connections
    logger.info("Initializing Redis connections...")
    
    # Start background tasks
    logger.info("Starting background tasks...")
    
    # Validate configuration
    logger.info("Validating configuration...")
    
    logger.info("Startup tasks completed")

async def shutdown_tasks():
    """
    Tasks to run on application shutdown
    """
    logger.info("Running shutdown tasks...")
    
    # Close database connections
    logger.info("Closing database connections...")
    
    # Close Redis connections
    logger.info("Closing Redis connections...")
    
    # Stop background tasks
    logger.info("Stopping background tasks...")
    
    logger.info("Shutdown tasks completed")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

# Add custom security middleware
SecurityMiddleware(app)

# Health checker instance
health_checker = HealthChecker()

# ==================================================
# 7. HEALTH CHECK ENDPOINTS
# ==================================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check endpoint
    """
    return await health_checker.perform_health_check()

@app.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes
    """
    # Perform basic checks
    db_healthy = (await health_checker.check_database())["status"] == "healthy"
    
    if db_healthy:
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics")
async def metrics():
    """
    Prometheus-style metrics endpoint
    """
    metrics_data = health_checker.get_system_metrics()
    
    # Convert to Prometheus format
    prometheus_metrics = f"""
# HELP cpu_usage_percent CPU usage percentage
# TYPE cpu_usage_percent gauge
cpu_usage_percent {metrics_data.cpu_usage}

# HELP memory_usage_percent Memory usage percentage
# TYPE memory_usage_percent gauge
memory_usage_percent {metrics_data.memory_usage}

# HELP disk_usage_percent Disk usage percentage
# TYPE disk_usage_percent gauge
disk_usage_percent {metrics_data.disk_usage}

# HELP process_count Number of processes
# TYPE process_count gauge
process_count {metrics_data.process_count}

# HELP open_files Number of open files
# TYPE open_files gauge
open_files {metrics_data.open_files}
"""
    
    return Response(content=prometheus_metrics, media_type="text/plain")

# ==================================================
# 8. CONFIGURATION ENDPOINTS
# ==================================================

@app.get("/config")
async def get_config():
    """
    Get application configuration (sanitized)
    """
    # Only return non-sensitive configuration
    config = {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "allowed_hosts": settings.allowed_hosts,
        "cors_origins": settings.cors_origins,
        "log_level": settings.log_level,
        "max_connections": settings.max_connections,
        "connection_timeout": settings.connection_timeout,
    }
    
    return config

# ==================================================
# 9. DOCKER CONFIGURATION
# ==================================================

# Dockerfile content
DOCKERFILE_CONTENT = """
# Multi-stage build for production
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health/live || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""

# Docker Compose configuration
DOCKER_COMPOSE_CONTENT = """
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
"""

# ==================================================
# 10. NGINX CONFIGURATION
# ==================================================

NGINX_CONFIG = """
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    server {
        listen 80;
        server_name example.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name example.com;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        
        # Apply rate limiting
        limit_req zone=api burst=20 nodelay;
        
        # Proxy configuration
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Health check
        location /health {
            access_log off;
            proxy_pass http://app;
        }
    }
}
"""

# ==================================================
# 11. KUBERNETES DEPLOYMENT
# ==================================================

K8S_DEPLOYMENT = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: fastapi-app
        image: fastapi-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
"""

# ==================================================
# 12. SAMPLE ENDPOINTS
# ==================================================

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running"
    }

@app.get("/version")
async def version():
    """
    Version information
    """
    return {
        "version": settings.app_version,
        "environment": settings.environment,
        "build_time": "2024-01-01T00:00:00Z",  # Set during build
        "git_commit": "abc123def456"  # Set during build
    }

"""
Production Deployment Checklist:

1. Environment Configuration:
   - Set all environment variables
   - Use strong secret keys
   - Configure database connections
   - Set up Redis for caching

2. Security:
   - Enable HTTPS
   - Set security headers
   - Configure CORS properly
   - Use non-root user in containers
   - Implement rate limiting

3. Performance:
   - Use multiple workers
   - Enable compression
   - Configure connection pooling
   - Set appropriate timeouts

4. Monitoring:
   - Health check endpoints
   - Metrics collection
   - Log aggregation
   - Error tracking

5. Scaling:
   - Horizontal scaling with load balancer
   - Auto-scaling based on metrics
   - Database read replicas
   - CDN for static assets

6. Backup & Recovery:
   - Database backups
   - Configuration backups
   - Disaster recovery plan
   - Regular restore testing

7. CI/CD:
   - Automated testing
   - Build pipeline
   - Deployment automation
   - Rollback procedures

Commands to Deploy:

1. Docker:
   docker build -t fastapi-app .
   docker run -p 8000:8000 fastapi-app

2. Docker Compose:
   docker-compose up -d

3. Kubernetes:
   kubectl apply -f deployment.yaml

4. Direct deployment:
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

Environment Variables:
- DATABASE_URL
- REDIS_URL
- SECRET_KEY
- ENVIRONMENT
- LOG_LEVEL
- CORS_ORIGINS
- ALLOWED_HOSTS
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 