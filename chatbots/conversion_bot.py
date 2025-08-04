import os
from typing import Dict, List, Optional, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
import json

from .prompts import CONVERSION_SYSTEM_PROMPT, CONVERSATION_TEMPLATES
from .utils import UserDataExtractor, ConversationManager, check_escalation_needed


class ConversationState(TypedDict):
    messages: Annotated[List, add_messages]
    user_profile: Dict
    message_count: int
    session_id: str
    escalation_needed: bool
    registration_suggested: bool


class ConversionChatbot:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self.extractor = UserDataExtractor(self.llm)
        self.conversation_manager = ConversationManager()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("analyze_message", self._analyze_message)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("check_escalation", self._check_escalation)
        workflow.add_node("suggest_registration", self._suggest_registration)
        workflow.add_node("escalate_to_human", self._escalate_to_human)
        
        # Set entry point
        workflow.set_entry_point("analyze_message")
        
        # Add edges
        workflow.add_edge("analyze_message", "check_escalation")
        
        # Conditional edge from check_escalation
        workflow.add_conditional_edges(
            "check_escalation",
            self._route_after_escalation_check,
            {
                "escalate": "escalate_to_human",
                "continue": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_response", 
            self._route_after_response,
            {
                "suggest_registration": "suggest_registration",
                "end": END
            }
        )
        
        workflow.add_edge("suggest_registration", END)
        workflow.add_edge("escalate_to_human", END)
        
        return workflow.compile()
    
    def _analyze_message(self, state: ConversationState) -> ConversationState:
        """Analyze the user's message and extract relevant information"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]
        if last_message.type != "human":
            return state
            
        # Extract user interests and data
        extracted_data = self.extractor.extract_interests(last_message.content)
        
        # Update user profile
        self.conversation_manager.update_user_profile(
            state["session_id"], 
            extracted_data
        )
        
        # Update state
        state["user_profile"] = self.conversation_manager.get_user_profile(state["session_id"])
        state["message_count"] = len([m for m in state["messages"] if m.type == "human"])
        
        return state
    
    def _check_escalation(self, state: ConversationState) -> ConversationState:
        """Check if the conversation needs to be escalated to a human agent"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]
        if last_message.type == "human":
            state["escalation_needed"] = check_escalation_needed(last_message.content)
        
        return state
    
    def _route_after_escalation_check(self, state: ConversationState) -> str:
        """Route based on escalation check"""
        return "escalate" if state["escalation_needed"] else "continue"
    
    def _generate_response(self, state: ConversationState) -> ConversationState:
        """Generate the main AI response"""
        # Prepare context for the AI
        user_profile = state["user_profile"]
        context_info = ""
        
        if user_profile.get("teams"):
            context_info += f"User's favorite teams: {', '.join(user_profile['teams'])}. "
        if user_profile.get("leagues"):
            context_info += f"User follows: {', '.join(user_profile['leagues'])}. "
        if user_profile.get("location"):
            context_info += f"User location: {user_profile['location']}. "
        
        # Build messages for the LLM
        system_message = SystemMessage(content=CONVERSION_SYSTEM_PROMPT)
        
        if context_info:
            system_message.content += f"\n\nCurrent user context: {context_info}"
        
        # Get conversation history (last 10 messages for context)
        recent_messages = state["messages"][-10:]
        llm_messages = [system_message] + recent_messages
        
        # Generate response
        try:
            response = self.llm.invoke(llm_messages)
            state["messages"].append(AIMessage(content=response.content))
        except Exception as e:
            # Fallback response
            fallback_response = "I apologize, but I'm having trouble processing your request right now. Could you please try again?"
            state["messages"].append(AIMessage(content=fallback_response))
            print(f"Error generating response: {e}")
        
        return state
    
    def _route_after_response(self, state: ConversationState) -> str:
        """Determine if we should suggest registration"""
        should_suggest = (
            not state.get("registration_suggested", False) and
            self.conversation_manager.should_suggest_registration(
                state["session_id"], 
                state["message_count"]
            )
        )
        
        return "suggest_registration" if should_suggest else "end"
    
    def _suggest_registration(self, state: ConversationState) -> ConversationState:
        """Add a registration suggestion to the conversation"""
        user_profile = state["user_profile"]
        
        # Customize registration message based on user interests
        if user_profile.get("teams"):
            favorite_team = user_profile["teams"][0]
            suggestion = CONVERSATION_TEMPLATES["registration_soft"].format(topic=favorite_team)
        else:
            suggestion = CONVERSATION_TEMPLATES["value_proposition"]
        
        # Add the suggestion as a follow-up message
        current_response = state["messages"][-1].content
        enhanced_response = f"{current_response}\n\n{suggestion}"
        
        # Update the last message
        state["messages"][-1] = AIMessage(content=enhanced_response)
        state["registration_suggested"] = True
        
        return state
    
    def _escalate_to_human(self, state: ConversationState) -> ConversationState:
        """Handle escalation to human agent"""
        escalation_message = CONVERSATION_TEMPLATES["escalation"]
        state["messages"].append(AIMessage(content=escalation_message))
        return state
    
    def chat(self, message: str, session_id: str, chat_history: List[Dict] = None) -> Dict:
        """Main chat interface"""
        # Initialize state
        initial_state = ConversationState(
            messages=[],
            user_profile={},
            message_count=0,
            session_id=session_id,
            escalation_needed=False,
            registration_suggested=False
        )
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    initial_state["messages"].append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
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
                response_content = "I'm here to help! What would you like to know about football betting?"
            
            return {
                "response": response_content,
                "user_profile": final_state["user_profile"],
                "escalation_needed": final_state.get("escalation_needed", False),
                "session_id": session_id
            }
            
        except Exception as e:
            print(f"Error in chat processing: {e}")
            return {
                "response": "I apologize, but I'm having some technical difficulties. Please try again or contact our support team if the problem persists.",
                "user_profile": {},
                "escalation_needed": False,
                "session_id": session_id
            }


# Singleton instance
_chatbot_instance = None

def get_conversion_chatbot() -> ConversionChatbot:
    """Get the singleton conversion chatbot instance"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ConversionChatbot()
    return _chatbot_instance