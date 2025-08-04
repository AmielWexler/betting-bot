# ⚽ AI Betting Assistant

A comprehensive football betting AI assistant powered by advanced language models, RAG (Retrieval-Augmented Generation), and intelligent user preference learning. The system features a dual-chatbot architecture designed to maximize user engagement and provide personalized betting insights.

## 🌟 Features

### 🤖 Dual Chatbot System
- **Conversion Chatbot**: Engages leads, collects user information, and guides through onboarding
- **Betting Chatbot**: Provides football betting insights, predictions, and personalized recommendations

### 🧠 Intelligent User Preference Learning
- **Automatic Preference Extraction**: Learns user preferences from natural language conversations
- **Team & League Detection**: Identifies favorite teams and leagues from user messages
- **Risk Tolerance Analysis**: Determines user risk appetite from conversation context
- **Persistent Storage**: Saves preferences to PostgreSQL for personalized experiences

### 📊 RAG-Powered Knowledge System
- **Vector Database Integration**: FAISS-powered document retrieval
- **Contextual Responses**: Combines user preferences with relevant football knowledge
- **Real-time Data Integration**: Supports live odds, team form, and match predictions
- **Extensible Knowledge Base**: Easy to add new football data and insights

### 🌐 Multi-Interface Support
- **Streamlit Web App**: User-friendly web interface with authentication
- **REST API**: FastAPI-powered backend for external integrations
- **Real-time Chat**: Session-based conversations with history tracking

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │   PostgreSQL    │
│   Frontend      │◄──►│      API        │◄──►│    Database     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│  LangGraph      │◄─────────────┘
                        │  Chatbots       │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   FAISS Vector  │
                        │   Database      │
                        │   (RAG System)  │
                        └─────────────────┘
```

### Core Components

1. **Frontend Layer**
   - Streamlit web application
   - User authentication and session management
   - Chat interfaces for both conversion and betting bots

2. **API Layer**
   - FastAPI REST endpoints
   - JWT authentication
   - CORS support for external integrations

3. **AI Processing Layer**
   - LangGraph workflow orchestration
   - Google Gemini 1.5 Flash integration
   - Dual chatbot system with specialized prompts

4. **Data Layer**
   - PostgreSQL for user data and preferences
   - FAISS vector database for knowledge retrieval
   - Structured football knowledge storage

5. **Intelligence Layer**
   - Preference extraction from natural language
   - RAG system for contextual responses
   - Real-time data integration tools

## 🛠️ Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Frontend**: Streamlit
- **Database**: PostgreSQL 15
- **AI/ML**: LangChain, LangGraph, Google Gemini, FAISS
- **Containerization**: Docker, Docker Compose
- **Authentication**: JWT, bcrypt
- **Vector Search**: Sentence Transformers, Hugging Face

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Google API key for Gemini
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd betting-bot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   Required environment variables:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   DATABASE_URL=postgresql://betting_user:betting_password@localhost:5433/betting_bot
   JWT_SECRET_KEY=your_jwt_secret_key_here
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Web Interface: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5433

### Manual Setup (Development)

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL**
   ```bash
   docker-compose up postgres -d
   ```

3. **Initialize the database**
   ```bash
   python -c "from database import db; print('DB Connected:', db.test_connection())"
   ```

4. **Run the application**
   ```bash
   # Start Streamlit app
   streamlit run app.py

   # Or start FastAPI server
   python start_api.py
   ```

## 📱 Usage Guide

### Web Interface

1. **Visit** http://localhost:8501
2. **Register** a new account or login
3. **Chat with the Conversion Bot** to get started
4. **Access the Betting Bot** after registration for personalized betting insights

### Example Interactions

**Conversion Bot:**
```
User: "Hi, I'm interested in football betting"
Bot: "Welcome! I'd love to help you get started. What's your experience with football betting?"
```

**Betting Bot:**
```
User: "I love Arsenal, give me some interesting bets for their next games. I like the adrenaline from the risk."
Bot: "Great! I can see you're an Arsenal fan with a high-risk appetite. Here are some exciting betting opportunities..."
```

The system will automatically:
- ✅ Extract "Arsenal" as a favorite team
- ✅ Detect "high risk" tolerance from "adrenaline" context
- ✅ Store preferences in PostgreSQL
- ✅ Personalize future recommendations

### API Usage

**Authentication:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

**Chat with Betting Bot:**
```bash
curl -X POST "http://localhost:8000/betting/chat" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the odds for Liverpool vs Manchester City?"}'
```

## 🧠 AI Features Deep Dive

### Intelligent Preference Extraction

The system automatically learns user preferences through natural language processing:

**Team Detection:**
- Recognizes 50+ major football teams
- Handles variations: "Man City", "Manchester City", "City"
- Detects context: "I love Arsenal", "betting on Chelsea"

**Risk Tolerance Analysis:**
- **High Risk**: "adrenaline", "thrill", "big stakes", "don't mind losing"
- **Medium Risk**: "balanced", "reasonable", "moderate"
- **Low Risk**: "safe", "conservative", "careful"

**League Preferences:**
- Premier League, La Liga, Serie A, Bundesliga, Champions League
- Contextual detection from team mentions and explicit statements

### RAG System

**Knowledge Retrieval:**
```python
# Example: User asks about Arsenal
query = "Arsenal recent form"
# System enhances with user context:
enhanced_query = "Arsenal recent form (user follows: Arsenal, Chelsea) (leagues: Premier League)"
# Retrieves relevant documents about Arsenal's performance
```

**Personalized Responses:**
- Combines retrieved knowledge with user preferences
- Adapts language and recommendations to risk tolerance
- Provides contextual insights based on favorite teams

## 📊 Database Schema

### Core Tables

**Users**
- Authentication and basic profile information
- Registration tracking and login history

**User Preferences**
- `favorite_teams`: TEXT[] - Array of favorite team names
- `favorite_leagues`: TEXT[] - Preferred leagues
- `betting_style`: VARCHAR - Betting approach preference
- `risk_tolerance`: VARCHAR - Risk appetite (low/medium/high)

**Chat Sessions**
- Conversation tracking for both chatbot types
- Session management and history

**Chat Messages**
- Complete conversation history
- Metadata storage for AI insights

**Knowledge Documents**
- Football knowledge base storage
- Document metadata and retrieval statistics

### Sample Data Structure

```sql
-- User preferences example
INSERT INTO user_preferences (user_id, favorite_teams, risk_tolerance)
VALUES (123, ARRAY['Arsenal', 'Chelsea'], 'high');

-- Retrieved as:
{
  "favorite_teams": ["Arsenal", "Chelsea"],
  "favorite_leagues": ["premier league"],
  "risk_tolerance": "high",
  "betting_style": "aggressive"
}
```

## 🔧 Development Guide

### 📁 Detailed File Structure

```
betting-bot/
├── 📄 Root Configuration Files
│   ├── app.py                          # 🎯 Main Streamlit web application entry point
│   ├── database.py                     # 🗄️ Database operations, models, and connection management
│   ├── schema.sql                      # 🏗️ PostgreSQL database schema and table definitions
│   ├── requirements.txt                # 📦 Python package dependencies
│   ├── docker-compose.yml              # 🐳 Docker services orchestration (PostgreSQL + App)
│   ├── Dockerfile                      # 📋 Container build instructions
│   ├── start_api.py                    # 🚀 FastAPI server startup script
│
├── 🌐 API Layer (FastAPI Backend)
│   └── api/
│       ├── __init__.py                 # 📦 Package initialization
│       ├── main.py                     # 🔧 FastAPI app setup, CORS, middleware
│       ├── auth.py                     # 🔐 JWT authentication, user verification
│       └── endpoints.py                # 🛣️ REST API route definitions and handlers
│
├── 🤖 AI Chatbot System
│   └── chatbots/
│       ├── __init__.py                 # 📦 Package initialization
│       ├── betting_bot.py              # ⚽ Main betting chatbot with LangGraph workflow
│       ├── conversion_bot.py           # 🎯 Lead conversion chatbot for user onboarding
│       ├── preference_extractor.py     # 🧠 NLP-powered user preference extraction
│       ├── rag_system.py               # 🔍 Retrieval-Augmented Generation implementation
│       ├── knowledge_base.py           # 📚 Football knowledge management and storage
│       ├── tools.py                    # 🔧 External API integrations (odds, stats, predictions)
│       ├── betting_prompts.py          # 💬 Specialized prompts for betting scenarios
│       ├── prompts.py                  # 📝 General chatbot prompt templates
│       └── utils.py                    # 🛠️ Utility functions and helpers
│
├── 📊 Data Storage & Knowledge Base
│   └── data/
│       ├── football_knowledge/         # ⚽ Structured football data repository
│       │   ├── betting/               # 💰 Betting-related documents and insights
│       │   │   ├── 0ad3e5eb44c9.json  # 📄 Sample betting analysis document
│       │   │   └── a7f0a18335fa.json  # 📄 Sample betting strategy document
│       │   ├── leagues/               # 🏆 League information and statistics
│       │   ├── matches/               # ⚽ Match data and historical results
│       │   │   └── fc7de67bf307.json  # 📄 Sample match analysis
│       │   ├── players/               # 👤 Player statistics and profiles
│       │   ├── statistics/            # 📈 General football statistics
│       │   └── teams/                 # 🏟️ Team information and performance data
│       │       ├── 7ad266b270b9.json  # 📄 Sample team analysis
│       │       └── b45854e9eced.json  # 📄 Sample team statistics
│       └── vector_store/              # 🔍 FAISS vector database storage
│           └── user_stores/           # 👥 User-specific vector stores
│
└── 🧪 Testing & Validation
    ├── test_preferences.py            # ✅ Preference extraction functionality tests
    ├── test_database_preferences.py   # ✅ Database integration and storage tests
    └── test_knowledge_init.py         # ✅ Knowledge base initialization tests
```

### 🔍 Key File Descriptions

#### **Core Application Files**

**`app.py`** - 🎯 **Streamlit Web Interface**
- Main entry point for the web application
- Handles user authentication and session management
- Provides chat interfaces for both conversion and betting bots
- Manages UI state and user interactions

**`database.py`** - 🗄️ **Database Layer**
- SQLAlchemy-based database operations
- User management (registration, authentication, preferences)
- Chat session and message storage
- Preference extraction and storage functions
- Database connection management and error handling

**`schema.sql`** - 🏗️ **Database Schema**
- Complete PostgreSQL table definitions
- Indexes for performance optimization
- Foreign key relationships and constraints
- Trigger functions for automatic timestamp updates

#### **API Backend (`api/`)**

**`main.py`** - 🔧 **FastAPI Application**
- FastAPI app initialization and configuration
- CORS middleware for cross-origin requests
- Error handling and response formatting
- Health check endpoints

**`auth.py`** - 🔐 **Authentication System**
- JWT token generation and validation
- Password hashing with bcrypt
- User login/logout functionality
- Protected route decorators

**`endpoints.py`** - 🛣️ **API Routes**
- RESTful endpoints for betting and conversion bots
- User preference management endpoints
- Chat history and session management
- Request/response models with Pydantic

#### **AI Chatbot System (`chatbots/`)**

**`betting_bot.py`** - ⚽ **Main Betting Chatbot**
- LangGraph workflow orchestration
- Multi-stage conversation processing:
  - User profile retrieval
  - Preference extraction and storage
  - Query categorization
  - Context retrieval from RAG system
  - Personalized response generation
- Integration with external betting tools
- Session management and conversation history

**`conversion_bot.py`** - 🎯 **Lead Conversion Bot**
- Specialized for user onboarding and engagement
- Collects user information and preferences
- Guides users through registration process
- Identifies conversion opportunities

**`preference_extractor.py`** - 🧠 **NLP Preference Engine**
- Natural language processing for preference detection
- Team name recognition (50+ major football teams)
- Risk tolerance analysis from conversation context
- League preference identification
- Betting style and market preference extraction
- Confidence scoring for extracted preferences

**`rag_system.py`** - 🔍 **RAG Implementation**
- FAISS vector database integration
- Document embedding and indexing
- Semantic search and retrieval
- Context-aware document ranking
- User-specific knowledge personalization

**`knowledge_base.py`** - 📚 **Knowledge Management**
- Football knowledge repository management
- Document categorization and storage
- Knowledge base initialization and updates
- Statistics and usage tracking

**`tools.py`** - 🔧 **External Integrations**
- Live odds API integration (placeholder)
- Team form and statistics retrieval
- Match prediction algorithms
- Player statistics and injury reports
- Betting tips generation

#### **Data Layer (`data/`)**

**`football_knowledge/`** - ⚽ **Structured Knowledge**
- **`betting/`**: Betting strategies, analysis, and insights
- **`leagues/`**: League information, standings, and statistics
- **`matches/`**: Historical match data and analysis
- **`players/`**: Player profiles, statistics, and performance data
- **`teams/`**: Team information, form, and tactical analysis
- **`statistics/`**: General football statistics and trends

**`vector_store/`** - 🔍 **Vector Database**
- FAISS index files for semantic search
- User-specific document embeddings
- Conversation history embeddings
- Preference-based document clustering

#### **Testing Suite**

**`test_preferences.py`** - ✅ **Preference Testing**
- Tests for natural language preference extraction
- Team and league detection validation
- Risk tolerance analysis verification
- Confidence scoring accuracy tests

**`test_database_preferences.py`** - ✅ **Database Testing**
- End-to-end preference storage testing
- Database connection and transaction tests
- User creation and preference management
- PostgreSQL array handling validation

**`test_knowledge_init.py`** - ✅ **Knowledge Base Testing**
- Knowledge base initialization testing
- Document loading and indexing verification
- RAG system functionality testing
- Vector store performance validation

### 🔄 Data Flow Between Files

```
User Input (app.py) 
    ↓
Authentication (api/auth.py)
    ↓
Chatbot Selection (betting_bot.py OR conversion_bot.py)
    ↓
Preference Extraction (preference_extractor.py)
    ↓
Database Storage (database.py)
    ↓
Knowledge Retrieval (rag_system.py + knowledge_base.py)
    ↓
Tool Integration (tools.py)
    ↓
Response Generation (betting_bot.py)
    ↓
User Interface (app.py)
```

### 🏗️ Component Relationships

- **Frontend (app.py)** ↔ **API (api/)** ↔ **Database (database.py)**
- **Chatbots** ↔ **Preference Extractor** ↔ **Database**
- **RAG System** ↔ **Knowledge Base** ↔ **Vector Store**
- **Betting Bot** ↔ **External Tools** ↔ **Live Data Sources**
- **All Components** ↔ **PostgreSQL Database**

### Adding New Features

**1. New Preference Types:**
```python
# In preference_extractor.py
self.new_patterns = {
    "bet_size": ["small stake", "big bet", "£10", "$100"],
    "market_preference": ["over/under", "both teams score", "correct score"]
}
```

**2. New Knowledge Sources:**
```python
# In knowledge_base.py
def add_new_knowledge_category(self, category: str, documents: List[Dict]):
    for doc in documents:
        self.add_document(doc['content'], doc['title'], category)
```

**3. New API Endpoints:**
```python
# In api/endpoints.py
@router.post("/betting/analyze-match")
async def analyze_match(match_data: MatchData, current_user: dict = Depends(get_current_user)):
    # Implementation here
    pass
```

### Testing

**Run Preference Extraction Tests:**
```bash
python test_preferences.py
```

**Run Database Integration Tests:**
```bash
python test_database_preferences.py
```

**Test API Endpoints:**
```bash
# Start the API server
python start_api.py

# Run API tests
curl -X GET "http://localhost:8000/health"
```

### Adding New Teams/Leagues

**Update Preference Extractor:**
```python
# In preference_extractor.py
self.team_patterns.update({
    "new_team_name",
    "another_team",
    # Add more teams
})

self.league_patterns["new_league"] = ["new league", "alternative name"]
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
DATABASE_URL=postgresql://betting_user:betting_password@localhost:5433/betting_bot
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=betting_bot
POSTGRES_USER=betting_user
POSTGRES_PASSWORD=betting_password

# Authentication
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit Configuration
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_PORT=8501

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
```

### Docker Configuration

**Production Override:**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  streamlit:
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARNING
    restart: unless-stopped
  
  postgres:
    volumes:
      - /var/lib/postgresql/data
    restart: unless-stopped
```

**Development Override:**
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  streamlit:
    volumes:
      - .:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

Usage:
```bash
# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## 📚 API Documentation

### Authentication Endpoints

**POST /auth/register**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "message": "User created successfully"
}
```

**POST /auth/login**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user_info": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John"
  }
}
```

### Betting Endpoints

**POST /betting/chat**
```json
{
  "message": "What are Arsenal's chances against Chelsea?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "Based on recent form and your preference for Arsenal...",
  "user_profile": {
    "favorite_teams": ["Arsenal"],
    "risk_tolerance": "high"
  },
  "query_category": "match_prediction",
  "context_sources": ["arsenal_recent_form.json", "chelsea_stats.json"],
  "session_id": "uuid-session-id",
  "tools_used": ["get_team_form", "get_match_predictions"]
}
```

**GET /betting/preferences**
```json
{
  "favorite_teams": ["Arsenal", "Liverpool"],
  "favorite_leagues": ["premier league", "champions league"],
  "risk_tolerance": "high",
  "betting_style": "aggressive",
  "preferred_markets": ["over_under", "both_teams_score"]
}
```

**PUT /betting/preferences**
```json
{
  "favorite_teams": ["Arsenal", "Chelsea"],
  "risk_tolerance": "medium"
}
```

### Conversion Bot Endpoints

**POST /conversion/chat**
```json
{
  "message": "I'm interested in football betting",
  "lead_id": "optional-lead-id"
}
```

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**2. Google API Key Issues**
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Test API key
python -c "
from langchain_google_genai import ChatGoogleGenerativeAI
import os
llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', google_api_key=os.getenv('GOOGLE_API_KEY'))
print('API Key works!')
"
```

**3. Preference Extraction Not Working**
```bash
# Test preference extraction
python test_preferences.py

# Check logs in the application
# Look for messages like:
# 🔍 Preference extraction from: 'user message'
# 📊 Extracted: {...}
```

**4. RAG System Issues**
```bash
# Test knowledge base initialization
python test_knowledge_init.py

# Check FAISS vector store
python -c "
from chatbots.rag_system import get_rag_system
rag = get_rag_system()
print(rag.get_stats())
"
```

**5. Docker Issues**
```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Check container logs
docker-compose logs streamlit
docker-compose logs postgres
```

### Performance Optimization

**Database Indexing:**
```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_user_preferences_teams 
ON user_preferences USING GIN (favorite_teams);

CREATE INDEX CONCURRENTLY idx_chat_messages_user_timestamp 
ON chat_messages (user_id, timestamp DESC);
```

**Vector Store Optimization:**
```python
# Increase FAISS performance
from chatbots.rag_system import get_rag_system
rag = get_rag_system()
rag.optimize_index()  # Rebuild with better parameters
```

### Debugging Tips

**Enable Debug Logging:**
```python
# In your .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Or in Python code
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Database Query Debugging:**
```python
# Enable SQLAlchemy logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Workflow

1. **Setup Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

2. **Run Tests**
   ```bash
   python test_preferences.py
   python test_database_preferences.py
   ```

3. **Code Style**
   - Follow PEP 8 conventions
   - Use type hints where possible
   - Add docstrings for functions and classes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔮 Roadmap

- [ ] **Multi-language Support**: Support for Spanish, French, Italian
- [ ] **Advanced Analytics**: User betting pattern analysis and insights  
- [ ] **Mobile App**: React Native mobile application
- [ ] **Social Features**: Share bets and insights with friends
- [ ] **Advanced Risk Management**: Sophisticated bankroll management tools
- [ ] **Live Betting Integration**: Real-time in-play betting suggestions
- [ ] **Machine Learning Predictions**: Custom ML models for match outcomes
- [ ] **Webhook Integration**: Real-time notifications and updates

## 📞 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

---
