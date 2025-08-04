from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from .endpoints import router as betting_router
from .auth import authenticate_user, create_access_token, get_current_user
from database import db

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Betting Assistant API",
    description="REST API for the Football Betting AI Assistant with RAG capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request/Response models
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: dict

class ErrorResponse(BaseModel):
    detail: str
    timestamp: datetime
    path: str

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="Internal server error",
            timestamp=datetime.utcnow(),
            path=str(request.url.path)
        ).dict()
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check for the API"""
    try:
        db_healthy = db.test_connection()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
            "database": "connected" if db_healthy else "disconnected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
        )

# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token
    
    The token can be used for subsequent API calls by including it
    in the Authorization header as: Bearer <token>
    """
    try:
        user = authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=60 * 24)  # 24 hours
        access_token = create_access_token(
            data={"sub": user["email"], "user_id": user["id"]},
            expires_delta=access_token_expires
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=60 * 60 * 24,  # 24 hours in seconds
            user_info={
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/auth/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """
    Validate JWT token and return user information
    
    Use this endpoint to check if a token is still valid and get
    current user information.
    """
    return {
        "valid": True,
        "user_info": {
            "id": current_user["id"],
            "email": current_user["email"],
            "first_name": current_user["first_name"],
            "last_name": current_user["last_name"]
        },
        "timestamp": datetime.utcnow()
    }

# Include betting router
app.include_router(betting_router)

# API information endpoint
@app.get("/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "name": "AI Betting Assistant API",
        "version": "1.0.0",
        "description": "REST API for football betting AI assistant with RAG capabilities",
        "endpoints": {
            "authentication": [
                "/auth/login - Authenticate and get JWT token",
                "/auth/validate - Validate JWT token"
            ],
            "betting": [
                "/api/v1/chat - Chat with betting assistant",
                "/api/v1/chat/history/{session_id} - Get chat history",
                "/api/v1/system/stats - Get system statistics",
                "/api/v1/system/health - System health check"
            ],
            "knowledge": [
                "/api/v1/knowledge - Add knowledge documents",
                "/api/v1/knowledge/search - Search knowledge base"
            ],
            "external": [
                "/api/v1/external/chat - External API access (requires API key)"
            ]
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "authentication": {
            "type": "JWT Bearer Token",
            "header": "Authorization: Bearer <token>",
            "expiry": "24 hours"
        },
        "rate_limits": {
            "authenticated_users": "100 requests per hour",
            "external_api": "Configurable per API key"
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting AI Betting Assistant API...")
    
    # Test database connection
    if not db.test_connection():
        print("❌ Database connection failed!")
    else:
        print("✅ Database connected successfully")
    
    # Initialize betting chatbot (this will also initialize RAG system)
    try:
        from chatbots.betting_bot import get_betting_chatbot
        betting_bot = get_betting_chatbot()
        stats = betting_bot.get_knowledge_stats()
        print(f"✅ Betting chatbot initialized with {stats.get('knowledge_base', {}).get('total_documents', 0)} documents")
    except Exception as e:
        print(f"❌ Error initializing betting chatbot: {e}")
    
    print("🎯 API ready for requests!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down AI Betting Assistant API...")
    print("👋 Goodbye!")

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    print(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )