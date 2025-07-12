#!/usr/bin/env python3
"""
🚀 FastAPI Learning Journey - Quick Start Script

This script helps you get started with your FastAPI learning journey.
Run this script to see available examples and how to run them.
"""

import os
import sys
import subprocess

def print_banner():
    """Print welcome banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🚀 FastAPI Learning Journey 🚀                ║
    ║                                                              ║
    ║   Welcome to your comprehensive FastAPI learning guide!     ║
    ║   This will take you from beginner to advanced level.       ║
    ║                                                              ║
    ║   📚 COMPLETE LEARNING PATH NOW AVAILABLE! 📚                ║
    ║   • Beginner Level (5 files) ✅                              ║
    ║   • Intermediate Level (5 files) ✅                          ║
    ║   • Advanced Level (5 files) ✅                              ║
    ║                                                              ║
    ║   🎉 ALL 15 TUTORIAL FILES COMPLETE! 🎉                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ All required dependencies are installed!")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install dependencies first:")
        print("   pip install -r requirements.txt")
        return False

def list_learning_files():
    """List all available learning files."""
    beginner_files = [
        ("01_introduction.py", "FastAPI basics and first API"),
        ("02_first_api.py", "HTTP methods and status codes"),
        ("03_path_parameters.py", "URL parameters and validation"),
        ("04_query_parameters.py", "Query parameters and filtering"),
        ("05_request_body.py", "POST data and Pydantic models")
    ]
    
    intermediate_files = [
        ("06_response_models.py", "Response models and serialization"),
        ("07_error_handling.py", "Exception handling and custom errors"),
        ("08_dependency_injection.py", "Dependency injection system"),
        ("09_authentication.py", "Authentication and security"),
        ("10_database_integration.py", "Database operations with SQLAlchemy")
    ]
    
    advanced_files = [
        ("11_middleware.py", "Custom middleware and CORS"),
        ("12_background_tasks.py", "Async operations and task queues"),
        ("13_testing.py", "Unit and integration testing"),
        ("14_production_deployment.py", "Production deployment and Docker"),
        ("15_advanced_features.py", "WebSockets, SSE, and streaming")
    ]
    
    print("\n📚 BEGINNER LEVEL (Start here!):")
    for file, description in beginner_files:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"   {status} {file:<30} - {description}")
    
    print("\n🎯 INTERMEDIATE LEVEL (After completing beginner):")
    for file, description in intermediate_files:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"   {status} {file:<30} - {description}")
    
    print("\n🚀 ADVANCED LEVEL (Production-ready skills):")
    for file, description in advanced_files:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"   {status} {file:<30} - {description}")
    
    print("\n🚀 QUICK START GUIDE:")
    print("   1. Complete beginner level first (01-05)")
    print("   2. Then move to intermediate level (06-10)")
    print("   3. Finally tackle advanced level (11-15)")
    print("   4. Run: uvicorn filename:app --reload")
    print("   5. Open: http://127.0.0.1:8000/docs")
    print("   6. Explore the interactive API documentation")

def run_example(filename):
    """Run a specific FastAPI example."""
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return
    
    module_name = filename.replace('.py', '')
    print(f"🚀 Starting {filename}...")
    print(f"📖 Open http://127.0.0.1:8000/docs to see the API documentation")
    print("🔄 The server will auto-reload when you make changes")
    print("⏹️  Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run(["uvicorn", f"{module_name}:app", "--reload"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to start the server. Make sure uvicorn is installed.")
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Happy learning!")

def show_learning_path():
    """Show the complete learning path."""
    print("\n🗺️  COMPLETE LEARNING PATH:")
    print("="*60)
    
    print("\n🟢 BEGINNER LEVEL (Master these first):")
    print("   01_introduction.py      - FastAPI fundamentals")
    print("   02_first_api.py         - HTTP methods & Pydantic")
    print("   03_path_parameters.py   - URL parameters & validation")
    print("   04_query_parameters.py  - Query params & filtering")
    print("   05_request_body.py      - POST data & file uploads")
    
    print("\n🟡 INTERMEDIATE LEVEL (Build on beginner knowledge):")
    print("   06_response_models.py   - Response validation & serialization")
    print("   07_error_handling.py    - Custom exceptions & error responses")
    print("   08_dependency_injection.py - Reusable components & services")
    print("   09_authentication.py    - JWT, OAuth2, API keys & security")
    print("   10_database_integration.py - SQLAlchemy, CRUD & relationships")
    
    print("\n🔴 ADVANCED LEVEL (Production-ready skills):")
    print("   11_middleware.py        - Custom middleware & CORS")
    print("   12_background_tasks.py  - Async operations & task queues")
    print("   13_testing.py          - Unit & integration testing")
    print("   14_production_deployment.py - Production deployment & Docker")
    print("   15_advanced_features.py - WebSockets, SSE & streaming")

def show_help():
    """Show help information."""
    print("\n📖 FastAPI Learning Guide:")
    print("="*50)
    print("🔹 Each file is a complete FastAPI application")
    print("🔹 Read the code comments for line-by-line explanations") 
    print("🔹 Run each file with: uvicorn filename:app --reload")
    print("🔹 Test APIs at: http://127.0.0.1:8000/docs")
    print("🔹 Follow the order: Beginner → Intermediate → Advanced")
    
    print("\n🎯 Learning Tips:")
    print("🔹 Start with 01_introduction.py and follow the sequence")
    print("🔹 Read ALL the comments - they explain everything")
    print("🔹 Try modifying the code to experiment")
    print("🔹 Use the interactive docs to test endpoints")
    print("🔹 Complete one level before moving to the next")
    print("🔹 Practice by building your own API using the patterns")

def show_level_info():
    """Show information about each level."""
    print("\n📊 LEVEL BREAKDOWN:")
    print("="*50)
    
    print("\n🟢 BEGINNER LEVEL - API Fundamentals:")
    print("   • FastAPI basics and automatic documentation")
    print("   • HTTP methods (GET, POST, PUT, DELETE)")
    print("   • Path and query parameters with validation")
    print("   • Request bodies and Pydantic models")
    print("   • File uploads and form data")
    print("   ⏱️  Time to complete: 3-5 hours")
    
    print("\n🟡 INTERMEDIATE LEVEL - Production Features:")
    print("   • Response models and data serialization")
    print("   • Error handling and custom exceptions")
    print("   • Dependency injection and service architecture")
    print("   • Authentication, JWT tokens, and security")
    print("   • Database integration with SQLAlchemy")
    print("   ⏱️  Time to complete: 8-12 hours")
    
    print("\n🔴 ADVANCED LEVEL - Production Ready:")
    print("   • Custom middleware, CORS, and request processing")
    print("   • Background tasks, async operations, and task queues")
    print("   • Comprehensive testing with pytest and mocking")
    print("   • Production deployment, Docker, and monitoring")
    print("   • WebSockets, Server-Sent Events, and streaming")
    print("   ⏱️  Time to complete: 10-15 hours")

def main():
    """Main function."""
    print_banner()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if not filename.endswith('.py'):
            filename += '.py'
        run_example(filename)
        return
    
    if not check_dependencies():
        return
    
    list_learning_files()
    show_learning_path()
    show_level_info()
    show_help()
    
    print("\n🚀 Quick Start Commands:")
    print("   python start_learning.py 01_introduction    # Start with basics")
    print("   python start_learning.py 02_first_api       # HTTP methods")
    print("   python start_learning.py 06_response_models # Intermediate level")
    print("   python start_learning.py 09_authentication  # Security features")
    print("   python start_learning.py 11_middleware      # Advanced middleware")
    print("   python start_learning.py 13_testing         # Testing strategies")
    print("   python start_learning.py 15_advanced_features # WebSockets & SSE")
    
    print("\n💡 What's New in This Update:")
    print("   ✨ Complete Advanced Level (5 new files)")
    print("   🔧 Custom middleware and CORS configuration")
    print("   ⚡ Background tasks and async operations")
    print("   🧪 Comprehensive testing with pytest")
    print("   🐳 Production deployment with Docker")
    print("   🌐 WebSockets, Server-Sent Events, and streaming")
    print("   📊 Health checks and monitoring")
    print("   🔒 Security best practices and rate limiting")
    
    print("\n🎉 You now have a complete FastAPI learning system!")
    print("   📚 15 comprehensive tutorial files")
    print("   🔧 Production-ready patterns and best practices")
    print("   💻 Real-world examples and use cases")
    print("   🎯 Step-by-step progression from beginner to expert")
    print("   🚀 Everything you need to build production APIs")

if __name__ == "__main__":
    main() 