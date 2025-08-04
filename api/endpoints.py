from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .auth import get_current_active_user, check_rate_limit, api_key_auth
from chatbots.betting_bot import get_betting_chatbot
from chatbots.knowledge_base import get_knowledge_manager
from chatbots.rag_system import get_rag_system
from database import db

# Create router
router = APIRouter(prefix="/api/v1", tags=["betting"])

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's betting query", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="Chat session ID for context")
    include_context: bool = Field(True, description="Whether to include RAG context in response")
    
class ChatResponse(BaseModel):
    response: str
    query_category: str
    context_sources: List[str]
    session_id: str
    metadata: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class KnowledgeDocument(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10)
    category: str = Field(..., regex="^(teams|players|matches|leagues|betting|statistics)$")
    source: str = Field("api", max_length=100)
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeResponse(BaseModel):
    document_id: str
    title: str
    category: str
    created_at: datetime
    status: str

class SystemStats(BaseModel):
    knowledge_base: Dict[str, Any]
    rag_system: Dict[str, Any]
    api_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserProfile(BaseModel):
    favorite_teams: Optional[List[str]] = None
    favorite_leagues: Optional[List[str]] = None
    betting_style: Optional[str] = Field(None, regex="^(conservative|moderate|aggressive)$")
    risk_tolerance: Optional[str] = Field(None, regex="^(low|medium|high)$")

# Betting Chat Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat_with_betting_bot(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    _: bool = Depends(check_rate_limit)
):
    """
    Chat with the football betting assistant
    
    This endpoint provides access to the AI betting assistant with RAG capabilities.
    The assistant can help with:
    - Team and player analysis
    - Match predictions and insights
    - Betting strategy recommendations
    - Market analysis and value betting opportunities
    """
    try:
        betting_bot = get_betting_chatbot()
        
        # Generate session ID if not provided
        session_id = request.session_id or f"api_{current_user['id']}_{int(datetime.utcnow().timestamp())}"
        
        # Get chat response
        result = betting_bot.chat(
            message=request.message,
            user_id=current_user["id"],
            session_id=session_id
        )
        
        return ChatResponse(
            response=result["response"],
            query_category=result["query_category"],
            context_sources=result["context_sources"] if request.include_context else [],
            session_id=result["session_id"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    limit: int = 50
):
    """Get chat history for a specific session"""
    try:
        # Verify session belongs to user or implement session sharing logic
        history = db.get_chat_history(int(session_id))
        
        # Filter to show only the last N messages
        return {
            "session_id": session_id,
            "messages": history[-limit:] if history else [],
            "total_messages": len(history) if history else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat history: {str(e)}"
        )

# Knowledge Management Endpoints
@router.post("/knowledge", response_model=KnowledgeResponse)
async def add_knowledge_document(
    document: KnowledgeDocument,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Add a new document to the knowledge base
    
    Requires authenticated user. The document will be added to both the 
    knowledge base and the RAG system for immediate availability.
    """
    try:
        knowledge_manager = get_knowledge_manager()
        betting_bot = get_betting_chatbot()
        
        # Add document to knowledge base
        doc_id = knowledge_manager.add_document(
            content=document.content,
            title=document.title,
            category=document.category,
            source=f"{document.source}_user_{current_user['id']}",
            metadata={
                "added_by": current_user["id"],
                "added_via": "api",
                **(document.metadata or {})
            }
        )
        
        # Add to RAG system
        doc_obj = knowledge_manager.get_document(doc_id)
        if doc_obj:
            betting_bot.add_knowledge_document(
                content=document.content,
                title=document.title,
                category=document.category,
                source=document.source
            )
        
        return KnowledgeResponse(
            document_id=doc_id,
            title=document.title,
            category=document.category,
            created_at=datetime.utcnow(),
            status="added"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding knowledge document: {str(e)}"
        )

@router.get("/knowledge/search")
async def search_knowledge(
    query: str = Field(..., min_length=1),
    category: Optional[str] = None,
    limit: int = Field(default=10, le=50),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Search the knowledge base"""
    try:
        knowledge_manager = get_knowledge_manager()
        
        results = knowledge_manager.search_documents(
            query=query,
            category=category,
            limit=limit
        )
        
        return {
            "query": query,
            "category": category,
            "results": [
                {
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "relevance": "high"  # Placeholder - implement actual relevance scoring
                }
                for doc in results
            ],
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge base: {str(e)}"
        )

# System Information Endpoints
@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get system statistics and health information"""
    try:
        betting_bot = get_betting_chatbot()
        stats = betting_bot.get_knowledge_stats()
        
        return SystemStats(
            knowledge_base=stats.get("knowledge_base", {}),
            rag_system=stats.get("rag_system", {}),
            api_status=stats.get("status", "unknown")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system stats: {str(e)}"
        )

@router.get("/system/health")
async def health_check():
    """Simple health check endpoint"""
    try:
        # Test database connection
        db_healthy = db.test_connection()
        
        # Test RAG system
        rag_system = get_rag_system()
        rag_stats = rag_system.get_stats()
        rag_healthy = rag_stats.get("status") == "ready"
        
        status_code = status.HTTP_200_OK if (db_healthy and rag_healthy) else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return {
            "status": "healthy" if (db_healthy and rag_healthy) else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "rag_system": "ready" if rag_healthy else "not_ready",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

# User Profile Endpoints
@router.get("/profile")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current user's profile and preferences"""
    try:
        profile = db.retrieve_user_info(current_user["id"])
        return {
            "user_info": profile,
            "api_access": True,
            "last_accessed": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}"
        )

@router.put("/profile")
async def update_user_profile(
    profile_update: UserProfile,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update user profile and betting preferences"""
    try:
        # This would require implementing update methods in the database
        # For now, return a placeholder response
        return {
            "message": "Profile update endpoint - implementation pending",
            "user_id": current_user["id"],
            "updates": profile_update.dict(exclude_none=True),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}"
        )

# External API Endpoints (using API key authentication)
@router.post("/external/chat")
async def external_chat_endpoint(
    request: ChatRequest,
    user_id: int,
    _: bool = Depends(api_key_auth)
):
    """
    External chat endpoint for third-party integrations
    
    Requires API key authentication. Allows external services to
    access the betting chatbot functionality.
    """
    try:
        betting_bot = get_betting_chatbot()
        
        # Generate session ID for external request
        session_id = request.session_id or f"external_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        result = betting_bot.chat(
            message=request.message,
            user_id=user_id,
            session_id=session_id
        )
        
        return {
            "response": result["response"],
            "query_category": result["query_category"],
            "session_id": result["session_id"],
            "source": "external_api",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing external chat request: {str(e)}"
        )