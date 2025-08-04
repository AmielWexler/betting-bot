#!/usr/bin/env python3
"""
Startup script for the AI Betting Assistant API
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_requirements():
    """Check if required environment variables are set"""
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file")
        return False
    
    return True

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting AI Betting Assistant API Server...")
    
    # Check if we can import the API
    try:
        from api.main import app
        print("✅ API module loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import API module: {e}")
        return False
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    print(f"🌐 Server will start on http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔄 Auto-reload: {'enabled' if reload else 'disabled'}")
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🎯 AI Betting Assistant - API Server Startup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Start API server
    if not start_api_server():
        sys.exit(1)

if __name__ == "__main__":
    main()