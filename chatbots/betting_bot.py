import os
from typing import Dict, List, Annotated, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .betting_prompts import (
    BETTING_CONVERSATION_TEMPLATES,
    get_personalized_prompt,
    format_response_with_context,
    get_query_category
)
from .rag_system import get_rag_system
from .knowledge_base import get_knowledge_manager
from .tools import get_all_tools
from .preference_extractor import extract_preferences_from_message
from database import db


class BettingConversationState(TypedDict):
    messages: Annotated[List, add_messages]
    user_id: int
    user_profile: Dict
    query_category: str
    retrieved_context: List[Dict]
    personalized_prompt: str
    session_id: str
    conversation_metadata: Dict
    tool_results: List[Dict]
    needs_tools: bool


class BettingChatbot:
    """Advanced football betting chatbot with RAG and personalization"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3  # Lower temperature for more consistent betting advice
        )
        
        self.rag_system = get_rag_system()
        self.knowledge_manager = get_knowledge_manager()
        self.tools = get_all_tools()
        
        # Ensure knowledge base is initialized with sample data
        self._initialize_knowledge_base()
        
        self.graph = self._build_graph()
    
    def _initialize_knowledge_base(self):
        """Initialize knowledge base with sample data if empty"""
        try:
            stats = self.knowledge_manager.get_statistics()
            if stats["total_documents"] == 0:
                print("Initializing knowledge base with sample data...")
                self.knowledge_manager.create_sample_knowledge()
                
                # Load documents into RAG system
                documents = self.knowledge_manager.get_all_documents()
                if documents:
                    self.rag_system.add_documents(documents)
                    print(f"Added {len(documents)} documents to RAG system")
        except Exception as e:
            print(f"Error initializing knowledge base: {e}")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow for betting queries"""
        workflow = StateGraph(BettingConversationState)
        
        # Add nodes
        workflow.add_node("retrieve_user_profile", self._retrieve_user_profile)
        workflow.add_node("extract_preferences", self._extract_preferences)
        workflow.add_node("categorize_query", self._categorize_query)
        workflow.add_node("check_tools_needed", self._check_tools_needed)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("personalize_prompt", self._personalize_prompt)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("store_interaction", self._store_interaction)
        
        # Set entry point
        workflow.set_entry_point("retrieve_user_profile")
        
        # Add edges with conditional routing
        workflow.add_edge("retrieve_user_profile", "extract_preferences")
        workflow.add_edge("extract_preferences", "categorize_query")
        workflow.add_edge("categorize_query", "check_tools_needed")
        workflow.add_conditional_edges(
            "check_tools_needed",
            self._should_use_tools,
            {
                "use_tools": "execute_tools",
                "skip_tools": "retrieve_context"
            }
        )
        workflow.add_edge("execute_tools", "retrieve_context")
        workflow.add_edge("retrieve_context", "personalize_prompt")
        workflow.add_edge("personalize_prompt", "generate_response")
        workflow.add_edge("generate_response", "store_interaction")
        workflow.add_edge("store_interaction", END)
        
        return workflow.compile()
    
    def _retrieve_user_profile(self, state: BettingConversationState) -> BettingConversationState:
        """Retrieve user profile and preferences from database"""
        try:
            # Get basic user info
            user_info = db.retrieve_user_info(state["user_id"])
            
            # Get enhanced preferences
            user_preferences = db.get_user_preferences(state["user_id"])
            
            if user_info and user_preferences:
                # Merge user info with preferences
                state["user_profile"] = {
                    **user_info,
                    **user_preferences
                }
            elif user_info:
                # Use basic user info
                state["user_profile"] = user_info
            else:
                # Default profile for testing
                state["user_profile"] = {
                    "id": state["user_id"],
                    "language": "en",
                    "favorite_teams": [],
                    "favorite_leagues": [],
                    "betting_style": "moderate",
                    "risk_tolerance": "medium"
                }
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            state["user_profile"] = {"id": state["user_id"], "language": "en"}
        
        return state
    
    def _extract_preferences(self, state: BettingConversationState) -> BettingConversationState:
        """Extract and store user preferences from the current message"""
        if not state["messages"]:
            return state
        
        last_message = state["messages"][-1]
        if last_message.type != "human":
            return state
        
        try:
            # Get conversation history for context
            user_history = ""
            for msg in state["messages"][-5:-1]:  # Last 5 messages for context
                if msg.type == "human":
                    user_history += f" {msg.content}"
            
            # Extract preferences from current message
            extracted = extract_preferences_from_message(last_message.content, user_history)
            
            # Debug logging
            print(f"🔍 Preference extraction from: '{last_message.content}'")
            print(f"📊 Extracted: {extracted}")
            
            # Only process if we found preferences with reasonable confidence
            if extracted["has_preferences"] and extracted["confidence"] > 0.1:
                print(f"✅ Processing preferences (confidence: {extracted['confidence']:.2f})")
                user_id = state["user_id"]
                
                # Update user preferences in database
                if extracted["teams"] or extracted["leagues"] or extracted["risk_tolerance"]:
                    success = db.update_user_preferences(
                        user_id=user_id,
                        favorite_teams=extracted["teams"] if extracted["teams"] else None,
                        favorite_leagues=extracted["leagues"] if extracted["leagues"] else None,
                        risk_tolerance=extracted["risk_tolerance"],
                        betting_style=extracted["betting_style"]
                    )
                    
                    if success:
                        print(f"✅ Updated preferences for user {user_id}: {extracted}")
                    else:
                        print(f"❌ Failed to update preferences for user {user_id}: {extracted}")
                
                # Update betting preferences if bet types were found
                if extracted["bet_types"]:
                    db.update_betting_preferences(
                        user_id=user_id,
                        favorite_bet_types=extracted["bet_types"],
                        risk_tolerance=extracted["risk_tolerance"]
                    )
                
                # Store extracted preferences in state for this conversation
                state["conversation_metadata"] = state.get("conversation_metadata", {})
                state["conversation_metadata"]["extracted_preferences"] = extracted
            else:
                print(f"⏭️ Skipped preferences (confidence: {extracted['confidence']:.2f} <= 0.1 or no preferences)")
        
        except Exception as e:
            print(f"❌ Error extracting preferences: {e}")
        
        return state
    
    def _categorize_query(self, state: BettingConversationState) -> BettingConversationState:
        """Categorize the user's query to determine response strategy"""
        if not state["messages"]:
            state["query_category"] = "general"
            return state
        
        last_message = state["messages"][-1]
        if last_message.type == "human":
            state["query_category"] = get_query_category(last_message.content)
        else:
            state["query_category"] = "general"
        
        return state
    
    def _retrieve_context(self, state: BettingConversationState) -> BettingConversationState:
        """Retrieve relevant context from the knowledge base using RAG"""
        if not state["messages"]:
            state["retrieved_context"] = []
            return state
        
        last_message = state["messages"][-1]
        if last_message.type != "human":
            state["retrieved_context"] = []
            return state
        
        try:
            # Enhance query with user context for better retrieval
            enhanced_query = self._enhance_query_with_context(
                last_message.content, 
                state["user_profile"]
            )
            
            # Retrieve relevant documents
            relevant_docs = self.rag_system.retrieve_relevant_documents(
                enhanced_query, 
                k=5
            )
            
            state["retrieved_context"] = relevant_docs
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            state["retrieved_context"] = []
        
        return state
    
    def _enhance_query_with_context(self, query: str, user_profile: Dict) -> str:
        """Enhance user query with their profile context for better retrieval"""
        enhanced_query = query
        
        # Add favorite teams context
        if user_profile.get("favorite_teams"):
            teams = ", ".join(user_profile["favorite_teams"])
            enhanced_query += f" (user follows: {teams})"
        
        # Add favorite leagues context
        if user_profile.get("favorite_leagues"):
            leagues = ", ".join(user_profile["favorite_leagues"])
            enhanced_query += f" (leagues: {leagues})"
        
        return enhanced_query
    
    def _check_tools_needed(self, state: BettingConversationState) -> BettingConversationState:
        """Check if external tools are needed for this query"""
        if not state["messages"]:
            state["needs_tools"] = False
            state["tool_results"] = []
            return state
        
        last_message = state["messages"][-1]
        if last_message.type != "human":
            state["needs_tools"] = False
            state["tool_results"] = []
            return state
        
        query = last_message.content.lower()
        
        # Keywords that suggest tool usage is needed
        tool_keywords = {
            "odds": ["odds", "betting odds", "bookmaker", "bet365", "william hill"],
            "live": ["live", "current", "now", "happening", "real-time"],
            "form": ["form", "recent", "last matches", "performance"],
            "stats": ["stats", "statistics", "goals", "assists", "cards"],
            "prediction": ["predict", "forecast", "who will win", "outcome"],
            "tips": ["tips", "advice", "recommend", "should i bet"]
        }
        
        needs_tools = any(
            any(keyword in query for keyword in keywords)
            for keywords in tool_keywords.values()
        )
        
        state["needs_tools"] = needs_tools
        state["tool_results"] = []
        
        return state
    
    def _should_use_tools(self, state: BettingConversationState) -> str:
        """Conditional routing function to decide if tools should be used"""
        return "use_tools" if state.get("needs_tools", False) else "skip_tools"
    
    def _execute_tools(self, state: BettingConversationState) -> BettingConversationState:
        """Execute relevant tools based on the query"""
        if not state["messages"] or not state.get("needs_tools", False):
            state["tool_results"] = []
            return state
        
        last_message = state["messages"][-1]
        query = last_message.content.lower()
        
        tool_results = []
        
        try:
            # Determine which tools to execute based on query content
            if any(keyword in query for keyword in ["odds", "betting odds"]):
                # Extract team names or use placeholder
                match_id = "sample_match_123"  # In production, extract from query
                from .tools import get_live_odds
                result = get_live_odds.invoke({"match_id": match_id})
                tool_results.append({
                    "tool": "get_live_odds",
                    "result": result,
                    "success": True
                })
            
            if any(keyword in query for keyword in ["form", "recent", "performance"]):
                # Extract team name or use placeholder
                team_name = "Liverpool"  # In production, extract from query using NER
                from .tools import get_team_form
                result = get_team_form.invoke({"team_name": team_name})
                tool_results.append({
                    "tool": "get_team_form",
                    "result": result,
                    "success": True
                })
            
            if any(keyword in query for keyword in ["predict", "forecast", "who will win"]):
                home_team = "Liverpool"  # Extract from query
                away_team = "Manchester City"  # Extract from query
                from .tools import get_match_predictions
                result = get_match_predictions.invoke({
                    "home_team": home_team,
                    "away_team": away_team
                })
                tool_results.append({
                    "tool": "get_match_predictions",
                    "result": result,
                    "success": True
                })
            
            if any(keyword in query for keyword in ["tips", "advice", "recommend"]):
                league = "Premier League"  # Extract from query or user profile
                risk_level = state["user_profile"].get("risk_tolerance", "medium")
                from .tools import get_betting_tips
                result = get_betting_tips.invoke({
                    "league": league,
                    "risk_level": risk_level
                })
                tool_results.append({
                    "tool": "get_betting_tips",
                    "result": result,
                    "success": True
                })
            
            # Store user interaction if relevant
            if tool_results:
                user_id = str(state["user_id"])
                analysis_text = f"User query: {last_message.content}\nTools used: {[r['tool'] for r in tool_results]}"
                from .tools import store_user_bet_analysis
                store_result = store_user_bet_analysis.invoke({
                    "user_id": user_id,
                    "bet_analysis": analysis_text
                })
                # Don't add this to tool_results as it's just storage
        
        except Exception as e:
            print(f"Error executing tools: {e}")
            tool_results.append({
                "tool": "error",
                "result": f"Tool execution failed: {str(e)}",
                "success": False
            })
        
        state["tool_results"] = tool_results
        return state
    
    def _personalize_prompt(self, state: BettingConversationState) -> BettingConversationState:
        """Create personalized system prompt based on user profile and context"""
        
        # Build context from retrieved documents
        context_text = ""
        if state["retrieved_context"]:
            context_text = "\n\nRELEVANT CONTEXT:\n"
            for i, doc in enumerate(state["retrieved_context"]):
                context_text += f"\n[Context {i+1}] {doc['source']}:\n{doc['content']}\n"
        
        # Add tool results to context
        if state.get("tool_results"):
            context_text += "\n\nREAL-TIME DATA:\n"
            for i, tool_result in enumerate(state["tool_results"]):
                if tool_result.get("success", False):
                    context_text += f"\n[Tool {i+1}] {tool_result['tool']}:\n{tool_result['result']}\n"
        
        # Create personalized system prompt
        state["personalized_prompt"] = get_personalized_prompt(
            state["user_profile"],
            context_text
        )
        
        return state
    
    def _generate_response(self, state: BettingConversationState) -> BettingConversationState:
        """Generate the main AI response using personalized prompt and context"""
        
        # Build messages for the LLM
        system_message = SystemMessage(content=state["personalized_prompt"])
        
        # Get recent conversation history (last 10 messages for context)
        recent_messages = state["messages"][-10:]
        llm_messages = [system_message] + recent_messages
        
        try:
            # Generate response
            response = self.llm.invoke(llm_messages)
            
            # Add response to conversation
            state["messages"].append(AIMessage(content=response.content))
            
            # Store metadata about the response
            state["conversation_metadata"] = {
                "query_category": state["query_category"],
                "context_used": len(state["retrieved_context"]),
                "response_length": len(response.content),
                "user_preferences_applied": bool(state["user_profile"]),
                "sources_used": [doc["source"] for doc in state["retrieved_context"]]
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            # Fallback response
            fallback_response = format_response_with_context("error_response", {})
            state["messages"].append(AIMessage(content=fallback_response))
            
            state["conversation_metadata"] = {
                "error": str(e),
                "query_category": state["query_category"],
                "fallback_used": True
            }
        
        return state
    
    def _store_interaction(self, state: BettingConversationState) -> BettingConversationState:
        """Store the interaction in the database for future reference"""
        try:
            if state["session_id"] and len(state["messages"]) >= 2:
                # Get the last user message and AI response
                user_message = None
                ai_response = None
                
                for msg in reversed(state["messages"]):
                    if msg.type == "ai" and ai_response is None:
                        ai_response = msg.content
                    elif msg.type == "human" and user_message is None:
                        user_message = msg.content
                    
                    if user_message and ai_response:
                        break
                
                if user_message and ai_response:
                    # Create session if it doesn't exist
                    session_exists = hasattr(self, '_session_created') and self._session_created
                    if not session_exists:
                        try:
                            db.create_chat_session(
                                user_id=state["user_id"],
                                session_type='betting'
                            )
                            self._session_created = True
                        except Exception as e:
                            print(f"Error creating chat session: {e}")
                    
                    # Store the interaction
                    metadata = {
                        "query_category": state["query_category"],
                        "context_sources": [doc["source"] for doc in state["retrieved_context"]],
                        "user_profile_used": state["user_profile"],
                        **state.get("conversation_metadata", {})
                    }
                    
                    # Convert session_id to integer with proper validation
                    try:
                        session_id_int = int(state["session_id"])
                    except (ValueError, TypeError) as e:
                        print(f"Error converting session_id to int: {state['session_id']} - {e}")
                        return state  # Skip storing if session_id is invalid
                    
                    # Add user message
                    db.add_chat_message(
                        session_id=session_id_int,
                        message=user_message,
                        sender="user",
                        message_type="betting_query",
                        metadata={"category": state["query_category"]}
                    )
                    
                    # Add AI response
                    db.add_chat_message(
                        session_id=session_id_int,
                        message=ai_response,
                        sender="bot",
                        message_type="betting_response",
                        metadata=metadata
                    )
        
        except Exception as e:
            print(f"Error storing interaction: {e}")
        
        return state
    
    def chat(self, message: str, user_id: int, session_id: str, 
             chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Main chat interface for betting queries"""
        
        # Initialize state
        initial_state = BettingConversationState(
            messages=[],
            user_id=user_id,
            user_profile={},
            query_category="general",
            retrieved_context=[],
            personalized_prompt="",
            session_id=session_id,
            conversation_metadata={},
            tool_results=[],
            needs_tools=False
        )
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "user":
                    initial_state["messages"].append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    initial_state["messages"].append(AIMessage(content=msg["content"]))
        
        # Add current user message
        initial_state["messages"].append(HumanMessage(content=message))
        
        # Process through the graph
        try:
            final_state = self.graph.invoke(initial_state)
            
            # Get the AI's response
            ai_messages = [msg for msg in final_state["messages"] if msg.type == "ai"]
            if ai_messages:
                response_content = ai_messages[-1].content
            else:
                response_content = BETTING_CONVERSATION_TEMPLATES["welcome_back"]
            
            return {
                "response": response_content,
                "user_profile": final_state["user_profile"],
                "query_category": final_state["query_category"],
                "context_sources": [doc["source"] for doc in final_state["retrieved_context"]],
                "session_id": session_id,
                "metadata": final_state.get("conversation_metadata", {}),
                "tools_used": [tool["tool"] for tool in final_state.get("tool_results", []) if tool.get("success", False)]
            }
            
        except Exception as e:
            print(f"Error in betting chat processing: {e}")
            return {
                "response": format_response_with_context("error_response", {}),
                "user_profile": {},
                "query_category": "error",
                "context_sources": [],
                "session_id": session_id,
                "metadata": {"error": str(e)},
                "tools_used": []
            }
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base and RAG system"""
        try:
            kb_stats = self.knowledge_manager.get_statistics()
            rag_stats = self.rag_system.get_stats()
            
            return {
                "knowledge_base": kb_stats,
                "rag_system": rag_stats,
                "status": "operational" if rag_stats.get("status") == "ready" else "initializing"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def add_knowledge_document(self, content: str, title: str, category: str, 
                              source: str = "manual") -> bool:
        """Add a new document to the knowledge base"""
        try:
            # Add to knowledge manager
            doc_id = self.knowledge_manager.add_document(
                content=content,
                title=title,
                category=category,
                source=source
            )
            
            # Get the document and add to RAG system
            document = self.knowledge_manager.get_document(doc_id)
            if document:
                self.rag_system.add_documents([document])
                return True
            
            return False
            
        except Exception as e:
            print(f"Error adding knowledge document: {e}")
            return False


# Singleton instance
_betting_chatbot = None

def get_betting_chatbot() -> BettingChatbot:
    """Get the singleton betting chatbot instance"""
    global _betting_chatbot
    if _betting_chatbot is None:
        _betting_chatbot = BettingChatbot()
    return _betting_chatbot