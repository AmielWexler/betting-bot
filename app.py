import streamlit as st
import os
from dotenv import load_dotenv
from database import db
from chatbots.conversion_bot import get_conversion_chatbot
import uuid
from datetime import datetime

load_dotenv()

st.set_page_config(
    page_title="AI Betting Assistant",
    page_icon="⚽",
    layout="wide"
)

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = None
    if 'conversion_session_id' not in st.session_state:
        st.session_state.conversion_session_id = str(uuid.uuid4())
    if 'chatbot_initialized' not in st.session_state:
        st.session_state.chatbot_initialized = False

def show_sidebar():
    with st.sidebar:
        st.title("⚽ AI Betting Assistant")
        
        if st.session_state.authenticated:
            st.success(f"Welcome, {st.session_state.user_info['first_name'] or st.session_state.user_info['email']}!")
            
            if st.button("🏆 Betting Chat", use_container_width=True):
                st.session_state.current_page = 'betting_chat'
                st.rerun()
            
            if st.button("👤 Profile", use_container_width=True):
                st.session_state.current_page = 'profile'
                st.rerun()
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.session_state.current_page = 'home'
                st.session_state.chat_session_id = None
                st.rerun()
        else:
            st.info("Connect with our AI betting assistant!")
            
            if st.button("💬 Start Chat", use_container_width=True):
                st.session_state.current_page = 'conversion_chat'
                st.rerun()
            
            if st.button("🔑 Login", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
            
            if st.button("📝 Register", use_container_width=True):
                st.session_state.current_page = 'register'
                st.rerun()

def show_home():
    st.title("🏆 Welcome to AI Betting Assistant")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("⚽ Football Betting Intelligence")
        st.write("""
        Get expert insights and analysis for football betting:
        - Real-time match analysis
        - Team form and statistics
        - Betting recommendations
        - Personalized tips based on your preferences
        """)
        
        if not st.session_state.authenticated:
            if st.button("Start Chatting Now", type="primary", use_container_width=True):
                st.session_state.current_page = 'conversion_chat'
                st.rerun()
    
    with col2:
        st.header("🎯 Smart Betting Features")
        st.write("""
        - **Live Match Updates**: Real-time scores and statistics
        - **Predictive Analytics**: AI-powered match predictions
        - **Risk Management**: Smart betting strategies
        - **Portfolio Tracking**: Monitor your betting performance
        """)
        
        if st.session_state.authenticated:
            if st.button("Go to Betting Chat", type="primary", use_container_width=True):
                st.session_state.current_page = 'betting_chat'
                st.rerun()

def show_login():
    st.title("🔑 Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", type="primary")
        
        if submit:
            if email and password:
                user_info = db.authenticate_user(email, password)
                if user_info:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.session_state.current_page = 'betting_chat'
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            else:
                st.error("Please enter both email and password")
    
    st.write("Don't have an account?")
    if st.button("Register here"):
        st.session_state.current_page = 'register'
        st.rerun()

def show_register():
    st.title("📝 Register")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name")
            email = st.text_input("Email")
            age = st.number_input("Age", min_value=18, max_value=100, value=25)
            country = st.text_input("Country")
        
        with col2:
            last_name = st.text_input("Last Name")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            city = st.text_input("City")
        
        language = st.selectbox("Preferred Language", ["en", "es", "fr", "de", "it"])
        
        submit = st.form_submit_button("Register", type="primary")
        
        if submit:
            if not all([email, password, first_name]):
                st.error("Please fill in all required fields (Email, Password, First Name)")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                try:
                    user_id = db.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        age=age,
                        country=country,
                        city=city,
                        language=language
                    )
                    
                    if user_id:
                        st.success("Registration successful! Please login.")
                        st.session_state.current_page = 'login'
                        st.rerun()
                    else:
                        st.error("Registration failed. Email might already be in use.")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")
    
    st.write("Already have an account?")
    if st.button("Login here"):
        st.session_state.current_page = 'login'
        st.rerun()

def show_conversion_chat():
    st.title("💬 Chat with Our AI Assistant")
    st.write("Hi! I'm here to help you get started with football betting. Ask me anything!")
    
    # Initialize the chatbot
    if not st.session_state.chatbot_initialized:
        try:
            st.session_state.chatbot = get_conversion_chatbot()
            st.session_state.chatbot_initialized = True
        except Exception as e:
            st.error(f"Failed to initialize chatbot: {str(e)}")
            st.error("Please check your Google API key configuration in the .env file")
            return
    
    # Initialize conversation messages
    if 'conversion_messages' not in st.session_state:
        st.session_state.conversion_messages = [
            {"role": "assistant", "content": "Hello! Welcome to our AI Betting Assistant. I'm here to help you discover the best football betting opportunities. What brings you here today?"}
        ]
    
    # Display chat history
    for message in st.session_state.conversion_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Handle user input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.conversion_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Show thinking indicator
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get response from chatbot
                    chat_result = st.session_state.chatbot.chat(
                        message=prompt,
                        session_id=st.session_state.conversion_session_id,
                        chat_history=st.session_state.conversion_messages[:-1]  # Exclude the current message
                    )
                    
                    response = chat_result["response"]
                    user_profile = chat_result.get("user_profile", {})
                    escalation_needed = chat_result.get("escalation_needed", False)
                    
                    # Store conversation data if there's useful profile information
                    if user_profile and any(user_profile.values()):
                        # Create a chat session in DB if not exists
                        if not hasattr(st.session_state, 'db_session_id'):
                            lead_id = db.create_lead(source="streamlit_chat")
                            if lead_id:
                                st.session_state.db_session_id = db.create_chat_session(
                                    lead_id=lead_id, 
                                    session_type='conversion'
                                )
                                db.update_lead_interests(lead_id, user_profile)
                        
                        # Store the conversation data
                        if hasattr(st.session_state, 'db_session_id') and st.session_state.db_session_id:
                            db.store_conversation_data(st.session_state.db_session_id, user_profile)
                    
                    # Display response
                    st.write(response)
                    
                    # Handle escalation
                    if escalation_needed:
                        st.info("🤖 **Human Agent Request**: Your conversation has been flagged for human assistance. In a production environment, this would connect you to a live agent.")
                    
                    # Handle registration intent detection
                    if db.check_register_intent(prompt):
                        st.write("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Register Now", type="primary", key=f"reg_{len(st.session_state.conversion_messages)}"):
                                st.session_state.current_page = 'register'
                                st.rerun()
                        with col2:
                            if st.button("Continue Chatting", key=f"continue_{len(st.session_state.conversion_messages)}"):
                                pass
                                
                except Exception as e:
                    st.error(f"Error processing your message: {str(e)}")
                    response = "I apologize, but I'm having some technical difficulties. Please try again or contact our support team if the problem persists."
        
        # Add assistant response to chat history
        st.session_state.conversion_messages.append({"role": "assistant", "content": response})
        st.rerun()

def show_betting_chat():
    st.title("🏆 Football Betting Assistant")
    
    # Comprehensive error handling for user info access
    try:
        user_name = st.session_state.user_info.get('first_name', 'User')
        st.write(f"Welcome back, {user_name}! Ask me about football matches, betting tips, or team analysis!")
    except (AttributeError, KeyError, TypeError) as e:
        st.error("Session data error. Please log in again.")
        st.session_state.current_page = 'login'
        st.rerun()
        return
    
    # Initialize the betting chatbot with comprehensive error handling
    if 'betting_chatbot' not in st.session_state:
        with st.spinner("Initializing betting assistant..."):
            try:
                from chatbots.betting_bot import get_betting_chatbot
                st.session_state.betting_chatbot = get_betting_chatbot()
                st.session_state.betting_chatbot_initialized = True
                st.success("✅ Betting assistant ready!")
            except ImportError as e:
                st.error("❌ Missing dependencies for betting chatbot")
                st.error(f"Import error: {str(e)}")
                st.info("Please ensure all required packages are installed.")
                return
            except Exception as e:
                st.error("❌ Failed to initialize betting chatbot")
                st.error(f"Error details: {str(e)}")
                st.info("Please check your configuration and try refreshing the page.")
                
                # Provide recovery options
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Retry Initialization"):
                        if 'betting_chatbot' in st.session_state:
                            del st.session_state.betting_chatbot
                        st.rerun()
                with col2:
                    if st.button("🏠 Return to Home"):
                        st.session_state.current_page = 'home'
                        st.rerun()
                return
    
    # Create betting session ID with error handling
    if 'betting_session_id' not in st.session_state:
        try:
            # Create database session with comprehensive error handling
            try:
                user_id = st.session_state.user_info.get('id')
                if not user_id:
                    raise ValueError("User ID not found in session")
                
                db_session_id = db.create_chat_session(
                    user_id=user_id,
                    session_type='betting'
                )
                
                if db_session_id:
                    # Use the database session ID for both UUID tracking and database operations
                    st.session_state.betting_session_id = str(db_session_id)
                    st.session_state.db_betting_session_id = db_session_id
                else:
                    raise ValueError("Failed to create database session")
                
            except Exception as db_error:
                st.warning(f"⚠️ Database session creation failed: {str(db_error)}")
                st.info("Chat will continue without database logging.")
                st.session_state.db_betting_session_id = None
                # Keep UUID for non-database operations
                import uuid
                st.session_state.betting_session_id = str(uuid.uuid4())
                
        except Exception as session_error:
            st.error(f"❌ Session initialization failed: {str(session_error)}")
            # Use a fallback session ID
            st.session_state.betting_session_id = f"fallback_{datetime.now().timestamp()}"
    
    # Initialize messages with error handling
    if 'betting_messages' not in st.session_state:
        try:
            user_name = st.session_state.user_info.get('first_name', 'there')
        except (AttributeError, KeyError):
            user_name = "there"
        welcome_message = f"""Hello {user_name}! I'm your personal football betting assistant powered by AI and real-time knowledge. 

I can help you with:
🔍 **Team & Player Analysis** - Recent form, statistics, injury updates
📊 **Match Predictions** - Data-driven insights and betting opportunities  
💰 **Betting Strategy** - Value betting, bankroll management, risk assessment
⚽ **Football Intelligence** - League standings, head-to-head records, tactical analysis

What would you like to analyze today?"""
        
        st.session_state.betting_messages = [
            {"role": "assistant", "content": welcome_message}
        ]
    
    # Display system stats in sidebar
    with st.sidebar:
        st.subheader("🤖 System Info")
        try:
            if hasattr(st.session_state, 'betting_chatbot'):
                stats = st.session_state.betting_chatbot.get_knowledge_stats()
                st.metric("Knowledge Documents", stats.get('knowledge_base', {}).get('total_documents', 0))
                st.metric("RAG Status", stats.get('status', 'unknown'))
                
                with st.expander("Knowledge Categories"):
                    categories = stats.get('knowledge_base', {}).get('categories', {})
                    for category, count in categories.items():
                        st.write(f"**{category.title()}**: {count}")
        except:
            st.write("System info unavailable")
    
    # Display chat history
    for message in st.session_state.betting_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            if message["role"] == "assistant":
                # Show tools used if available
                if "tools_used" in message and message["tools_used"]:
                    with st.expander("🔧 Tools Used"):
                        for tool in message["tools_used"]:
                            st.write(f"• {tool.replace('_', ' ').title()}")
                
                # Show context sources if available
                if "context_sources" in message and message["context_sources"]:
                    with st.expander("📚 Sources Used"):
                        for source in message["context_sources"]:
                            st.write(f"• {source}")
    
    # Handle user input
    if prompt := st.chat_input("Ask about matches, teams, or betting strategies..."):
        # Add user message to chat
        st.session_state.betting_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Show thinking indicator and get response with comprehensive error handling
        with st.chat_message("assistant"):
            with st.spinner("Analyzing... 🤔"):
                response_data = None
                try:
                    # Validate session state before proceeding
                    if not hasattr(st.session_state, 'betting_chatbot'):
                        raise RuntimeError("Betting chatbot not properly initialized")
                    
                    user_id = st.session_state.user_info.get('id')
                    if not user_id:
                        raise ValueError("User ID not available")
                    
                    session_id = getattr(st.session_state, 'betting_session_id', 'fallback')
                    chat_history = st.session_state.betting_messages[:-1] if len(st.session_state.betting_messages) > 1 else []
                    
                    # Get response from betting chatbot with timeout handling
                    try:
                        chat_result = st.session_state.betting_chatbot.chat(
                            message=prompt,
                            user_id=user_id,
                            session_id=session_id,
                            chat_history=chat_history
                        )
                        
                        if not chat_result or not isinstance(chat_result, dict):
                            raise ValueError("Invalid response format from chatbot")
                        
                        response = chat_result.get("response", "I apologize, but I couldn't generate a proper response.")
                        query_category = chat_result.get("query_category", "general")
                        context_sources = chat_result.get("context_sources", [])
                        metadata = chat_result.get("metadata", {})
                        tools_used = chat_result.get("tools_used", [])
                        
                        # Display response
                        st.write(response)
                        
                        # Show query category badge
                        if query_category != "general":
                            st.badge(f"Category: {query_category.replace('_', ' ').title()}")
                        
                        # Show tools used if available
                        if tools_used:
                            with st.expander("🔧 External Tools Used"):
                                for tool in tools_used:
                                    st.write(f"• {tool.replace('_', ' ').title()}")
                        
                        # Show context sources if available
                        if context_sources:
                            with st.expander("📚 Knowledge Sources Used"):
                                for source in context_sources:
                                    st.write(f"• {source}")
                        
                        # Show metadata in debug mode
                        if st.session_state.get('debug_mode', False):
                            with st.expander("🔧 Debug Info"):
                                st.json(metadata)
                        
                        # Store response with metadata
                        response_data = {
                            "role": "assistant", 
                            "content": response,
                            "query_category": query_category,
                            "context_sources": context_sources,
                            "metadata": metadata,
                            "tools_used": tools_used
                        }
                        
                    except TimeoutError:
                        error_response = "⏱️ The request timed out. Please try with a simpler question or try again later."
                        st.warning("Request timeout")
                        st.write(error_response)
                        response_data = {"role": "assistant", "content": error_response, "error": "timeout"}
                        
                    except ConnectionError:
                        error_response = "🔌 Connection error. Please check your internet connection and try again."
                        st.warning("Connection issue")
                        st.write(error_response)
                        response_data = {"role": "assistant", "content": error_response, "error": "connection"}
                        
                    except ValueError as ve:
                        error_response = f"📝 Input validation error: {str(ve)}\n\nPlease rephrase your question."
                        st.warning("Input validation failed")
                        st.write(error_response)
                        response_data = {"role": "assistant", "content": error_response, "error": "validation"}
                        
                except RuntimeError as re:
                    error_response = f"⚙️ System error: {str(re)}\n\nPlease refresh the page and try again."
                    st.error("System runtime error")
                    st.write(error_response)
                    
                    # Provide recovery options
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Refresh Chat", key="refresh_runtime"):
                            if 'betting_chatbot' in st.session_state:
                                del st.session_state.betting_chatbot
                            st.rerun()
                    with col2:
                        if st.button("🆘 Report Issue", key="report_runtime"):
                            st.info("Please contact support with error details.")
                    
                    response_data = {"role": "assistant", "content": error_response, "error": "runtime"}
                    
                except Exception as e:
                    # Generic error handler with detailed logging
                    error_type = type(e).__name__
                    error_msg = str(e)
                    
                    error_response = f"🚨 Unexpected error ({error_type}): {error_msg}\n\nPlease try again or contact support if the issue persists."
                    st.error("Unexpected error occurred")
                    st.write(error_response)
                    
                    # Provide multiple recovery options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔄 Retry", key="retry_generic"):
                            st.rerun()
                    with col2:
                        if st.button("🧹 Clear Chat", key="clear_generic"):
                            st.session_state.betting_messages = st.session_state.betting_messages[:1]
                            st.rerun()
                    with col3:
                        if st.button("🏠 Home", key="home_generic"):
                            st.session_state.current_page = 'home'
                            st.rerun()
                    
                    response_data = {"role": "assistant", "content": error_response, "error": "generic"}
                
                # Ensure we always have response data
                if response_data is None:
                    response_data = {
                        "role": "assistant", 
                        "content": "I apologize, but something went wrong. Please try again.",
                        "error": "unknown"
                    }
        
        # Add assistant response to chat history
        st.session_state.betting_messages.append(response_data)
        st.rerun()
    
    # Add debug toggle in sidebar
    with st.sidebar:
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=False)
        
        if st.button("Clear Chat History"):
            st.session_state.betting_messages = st.session_state.betting_messages[:1]  # Keep welcome message
            st.rerun()
            
        if st.button("New Session"):
            # Clear current session and create new one
            if 'betting_session_id' in st.session_state:
                del st.session_state.betting_session_id
            if 'betting_messages' in st.session_state:
                del st.session_state.betting_messages
            st.rerun()

def show_profile():
    st.title("👤 Profile")
    
    user_info = st.session_state.user_info
    st.write(f"**Email:** {user_info['email']}")
    st.write(f"**Name:** {user_info['first_name']} {user_info['last_name'] or ''}")
    
    st.subheader("Account Settings")
    st.info("Profile editing functionality will be implemented here.")

def main():
    init_session_state()
    show_sidebar()
    
    if not db.test_connection():
        st.error("❌ Database connection failed. Please check your database configuration.")
        st.stop()
    
    if st.session_state.current_page == 'home':
        show_home()
    elif st.session_state.current_page == 'login':
        show_login()
    elif st.session_state.current_page == 'register':
        show_register()
    elif st.session_state.current_page == 'conversion_chat':
        show_conversion_chat()
    elif st.session_state.current_page == 'betting_chat' and st.session_state.authenticated:
        show_betting_chat()
    elif st.session_state.current_page == 'profile' and st.session_state.authenticated:
        show_profile()
    else:
        show_home()

if __name__ == "__main__":
    main()