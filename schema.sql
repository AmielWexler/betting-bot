-- AI Betting Assistant Database Schema

-- Users table - stores registered user information
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INTEGER,
    country VARCHAR(100),
    city VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leads table - tracks potential users before registration
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    phone VARCHAR(50),
    first_name VARCHAR(100),
    source VARCHAR(100),
    campaign VARCHAR(100),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    status VARCHAR(20) DEFAULT 'new',
    conversion_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Chat sessions table - tracks individual chat conversations
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('conversion', 'betting')),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table - stores individual messages in conversations
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    sender VARCHAR(20) NOT NULL CHECK (sender IN ('user', 'bot')),
    message_type VARCHAR(20) DEFAULT 'text',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- User preferences table - stores betting and app preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    favorite_teams TEXT[],
    favorite_leagues TEXT[],
    betting_style VARCHAR(50),
    risk_tolerance VARCHAR(20),
    notification_settings JSONB DEFAULT '{}',
    language_preference VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_type ON chat_sessions(session_type);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Betting queries table - tracks user betting-related queries and responses
CREATE TABLE betting_queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_category VARCHAR(50),
    response_text TEXT,
    context_sources TEXT[],
    confidence_score DECIMAL(3,2),
    user_feedback INTEGER CHECK (user_feedback BETWEEN 1 AND 5),
    query_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_metadata JSONB
);

-- Document metadata table - tracks knowledge base documents and their usage
CREATE TABLE document_metadata (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    source VARCHAR(100),
    content_hash VARCHAR(64),
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    retrieval_count INTEGER DEFAULT 0,
    last_retrieved TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- User betting preferences - enhanced preferences for betting recommendations
CREATE TABLE user_betting_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    preferred_markets TEXT[] DEFAULT '{}',
    max_stake_per_bet DECIMAL(10,2),
    bankroll_size DECIMAL(10,2),
    risk_tolerance VARCHAR(20) DEFAULT 'medium' CHECK (risk_tolerance IN ('low', 'medium', 'high')),
    favorite_bet_types TEXT[] DEFAULT '{}',
    blacklisted_teams TEXT[] DEFAULT '{}',
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RAG system usage statistics
CREATE TABLE rag_usage_stats (
    id SERIAL PRIMARY KEY,
    query_date DATE DEFAULT CURRENT_DATE,
    total_queries INTEGER DEFAULT 0,
    successful_retrievals INTEGER DEFAULT 0,
    average_context_docs DECIMAL(4,2),
    popular_categories JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Additional indexes for betting system
CREATE INDEX idx_betting_queries_user_id ON betting_queries(user_id);
CREATE INDEX idx_betting_queries_category ON betting_queries(query_category);
CREATE INDEX idx_betting_queries_timestamp ON betting_queries(query_timestamp);
CREATE INDEX idx_document_metadata_category ON document_metadata(category);
CREATE INDEX idx_document_metadata_source ON document_metadata(source);
CREATE INDEX idx_document_metadata_retrieval_count ON document_metadata(retrieval_count);
CREATE INDEX idx_user_betting_preferences_user_id ON user_betting_preferences(user_id);
CREATE INDEX idx_rag_usage_stats_date ON rag_usage_stats(query_date);

-- Apply update triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_metadata_updated_at BEFORE UPDATE ON document_metadata FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_betting_preferences_updated_at BEFORE UPDATE ON user_betting_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();