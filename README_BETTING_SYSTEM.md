# AI Betting Assistant - Complete System Documentation

## Overview

This is a comprehensive AI-powered football betting assistant system with RAG (Retrieval-Augmented Generation) capabilities, personalized recommendations, and external API access.

## System Architecture

### Core Components

1. **Part 1: Conversion Funnel Chatbot** (`chatbots/conversion_bot.py`)
   - Engages leads and guides through onboarding
   - Collects user preferences and information
   - Manages user registration flow

2. **Part 2: Betting Chatbot** (`chatbots/betting_bot.py`) - **NEW**
   - Advanced RAG-powered football betting assistant
   - Personalized recommendations based on user preferences
   - Real-time knowledge retrieval and analysis

3. **Part 3: Streamlit Frontend** (`app.py`)
   - Unified interface supporting both chatbots
   - User authentication and session management
   - Interactive chat interface with context sources

4. **Part 4: PostgreSQL Database** (`database.py` + `schema.sql`)
   - User management and preferences
   - Chat history and conversation tracking
   - Betting query analytics and document metadata

5. **Part 5: FastAPI External API** (`api/`) - **NEW**
   - REST API for external integrations
   - JWT authentication and rate limiting
   - Knowledge management endpoints

## New Features Implemented

### 🤖 Advanced RAG System
- **FAISS Vector Database**: Efficient similarity search for football knowledge
- **Hybrid Retrieval**: Combines vector search with BM25 for better results
- **Knowledge Categories**: Teams, players, matches, leagues, betting strategies
- **Auto-initialization**: Creates sample knowledge base on first run

### 🎯 Personalized Betting Assistant
- **User Context Integration**: Pulls preferences from PostgreSQL
- **Query Categorization**: Automatically categorizes betting queries
- **Context-Aware Responses**: Uses user's favorite teams and leagues
- **Responsible Gambling**: Built-in risk management and warnings

### 🌐 External API Access
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Prevents API abuse
- **Multiple Auth Methods**: JWT for users, API keys for external services
- **Comprehensive Endpoints**: Chat, knowledge management, system stats

### 📊 Enhanced Database Schema
- **Betting Queries Tracking**: Stores all betting-related conversations
- **Document Metadata**: Tracks knowledge base usage and retrieval
- **User Betting Preferences**: Extended preference system
- **RAG Usage Statistics**: Performance monitoring and analytics

## File Structure

```
betting-bot/
├── chatbots/
│   ├── __init__.py
│   ├── conversion_bot.py      # Part 1: Lead conversion chatbot
│   ├── betting_bot.py         # Part 2: RAG-powered betting assistant
│   ├── rag_system.py          # FAISS vector store and retrieval
│   ├── knowledge_base.py      # Document management system
│   ├── betting_prompts.py     # Specialized betting prompts
│   ├── prompts.py            # General prompts
│   └── utils.py              # Utility functions
├── api/                       # Part 5: External API
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── auth.py               # Authentication and security
│   └── endpoints.py          # API endpoints
├── data/
│   ├── football_knowledge/   # Knowledge base documents
│   └── vector_store/         # FAISS index files
├── app.py                    # Part 3: Streamlit frontend
├── database.py               # Part 4: PostgreSQL integration
├── schema.sql                # Enhanced database schema
├── docker-compose.yml        # Docker services
├── requirements.txt          # Python dependencies
├── test_knowledge_init.py    # Testing script
└── start_api.py             # API startup script
```

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql://betting_user:betting_password@localhost:5433/betting_bot

# Google AI
GOOGLE_API_KEY=your_google_ai_api_key

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# External API Keys (comma-separated)
VALID_API_KEYS=key1,key2,key3
```

### 3. Start Services

```bash
# Start PostgreSQL database
docker-compose up postgres -d

# Initialize and test the system
python test_knowledge_init.py

# Start Streamlit app
streamlit run app.py

# Start FastAPI server (separate terminal)
python start_api.py
```

## Usage Examples

### Streamlit Interface

1. **Anonymous Users**: Use conversion chatbot to explore and register
2. **Registered Users**: Access advanced betting assistant with RAG
3. **Interactive Features**: View knowledge sources, debug mode, session management

### API Endpoints

#### Authentication
```bash
# Login and get JWT token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

#### Chat with Betting Assistant
```bash
# Use JWT token for authenticated requests
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Liverpool'"'"'s recent form?", "include_context": true}'
```

#### Add Knowledge Document
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Manchester United Analysis",
    "content": "Recent performance and statistics...",
    "category": "teams",
    "source": "manual"
  }'
```

#### External API Access (API Key)
```bash
curl -X POST "http://localhost:8000/api/v1/external/chat" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Should I bet on Real Madrid tonight?",
    "user_id": 123
  }'
```

## Key Features

### 🔍 Intelligent Query Processing
- **Automatic Categorization**: Team analysis, match prediction, betting strategy
- **Context Retrieval**: Finds relevant documents from knowledge base
- **Personalized Responses**: Adapts to user preferences and history

### 📚 Knowledge Management
- **6 Categories**: Teams, players, matches, leagues, betting, statistics
- **Sample Data**: Pre-loaded with Liverpool, Man City, betting strategies
- **Dynamic Updates**: Add new documents via API or interface
- **Usage Tracking**: Monitor which documents are most helpful

### 🛡️ Security & Reliability
- **JWT Authentication**: Secure token-based auth with expiration
- **Rate Limiting**: Prevents API abuse (100 requests/hour)
- **Input Validation**: Pydantic models for request validation
- **Error Handling**: Comprehensive error responses and logging

### 📊 Analytics & Monitoring
- **Query Analytics**: Track popular queries and categories
- **Performance Metrics**: RAG system performance monitoring
- **User Behavior**: Conversation patterns and preferences
- **System Health**: Database and RAG system status monitoring

## Testing

### Run System Tests
```bash
# Test knowledge base initialization and RAG system
python test_knowledge_init.py

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/system/health
```

### Manual Testing Scenarios

1. **Knowledge Retrieval**: Ask about "Liverpool recent form"
2. **Betting Strategy**: Query "value betting strategy"
3. **Match Analysis**: Ask "Liverpool vs Manchester City prediction"
4. **Personalization**: Set favorite teams and see customized responses

## System Capabilities

### Betting Assistant Queries Supported:
- ✅ "What is Liverpool's recent form?"
- ✅ "Should I bet on Real Madrid tonight?"
- ✅ "When is PSG playing next?"
- ✅ "What are the best betting strategies?"
- ✅ "How should I manage my bankroll?"
- ✅ "Tell me about Premier League standings"

### RAG System Features:
- ✅ Vector similarity search with FAISS
- ✅ BM25 keyword search for hybrid retrieval
- ✅ Document chunking and embedding
- ✅ Context-aware response generation
- ✅ Source attribution and transparency

### API Capabilities:
- ✅ RESTful endpoints for all major functions
- ✅ JWT and API key authentication
- ✅ Rate limiting and security measures
- ✅ Comprehensive documentation with Swagger UI
- ✅ External integration support

## Responsible Gambling

The system includes built-in responsible gambling features:
- ⚠️ Risk warnings and bankroll management advice
- 📊 Emphasis on long-term strategy over quick wins
- 🛡️ Clear disclaimers about betting risks
- 📈 Focus on education and value betting principles

## Next Steps

Potential enhancements:
1. **Real-time Data Integration**: Live scores, odds, player stats
2. **Advanced Analytics**: Machine learning predictions
3. **Mobile App**: React Native or Flutter app
4. **WebSocket Support**: Real-time chat updates
5. **Multi-language Support**: Internationalization
6. **Advanced User Preferences**: More granular betting preferences

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review system health at `/health` and `/api/v1/system/health`
3. Run the test script: `python test_knowledge_init.py`
4. Check logs for detailed error information

---

🎯 **The AI Betting Assistant is now fully operational with RAG capabilities, personalized recommendations, and external API access!**