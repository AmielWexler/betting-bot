import json
import re
from typing import Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from .prompts import EXTRACTION_PROMPTS

class UserDataExtractor:
    def __init__(self, llm):
        self.llm = llm
    
    def extract_interests(self, message: str) -> Dict:
        """Extract user interests and demographics from conversation message"""
        try:
            prompt = EXTRACTION_PROMPTS["extract_interests"].format(message=message)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Try to parse JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to basic extraction if JSON parsing fails
                return self._basic_extraction(message)
                
        except Exception as e:
            print(f"Error extracting interests: {e}")
            return self._basic_extraction(message)
    
    def _basic_extraction(self, message: str) -> Dict:
        """Basic fallback extraction using regex patterns"""
        message_lower = message.lower()
        
        # Common football teams (basic list)
        teams = []
        team_patterns = [
            r'\b(manchester united|man united|united)\b',
            r'\b(manchester city|man city|city)\b', 
            r'\b(liverpool|reds)\b',
            r'\b(chelsea|blues)\b',
            r'\b(arsenal|gunners)\b',
            r'\b(tottenham|spurs)\b',
            r'\b(real madrid|madrid)\b',
            r'\b(barcelona|barca)\b',
            r'\b(bayern munich|bayern)\b',
            r'\b(psg|paris saint-germain)\b'
        ]
        
        for pattern in team_patterns:
            if re.search(pattern, message_lower):
                match = re.search(pattern, message_lower)
                teams.append(match.group(1))
        
        # Basic league detection
        leagues = []
        if any(term in message_lower for term in ['premier league', 'epl', 'english']):
            leagues.append('Premier League')
        if any(term in message_lower for term in ['la liga', 'spanish', 'spain']):
            leagues.append('La Liga')
        if any(term in message_lower for term in ['serie a', 'italian', 'italy']):
            leagues.append('Serie A')
        if any(term in message_lower for term in ['bundesliga', 'german', 'germany']):
            leagues.append('Bundesliga')
        
        # Basic location detection
        location = ""
        countries = ['uk', 'usa', 'spain', 'italy', 'germany', 'france', 'england']
        for country in countries:
            if country in message_lower:
                location = country
                break
        
        return {
            "teams": teams,
            "leagues": leagues, 
            "location": location,
            "demographics": "",
            "betting_info": ""
        }
    
    def check_registration_intent(self, message: str) -> str:
        """Analyze message for registration intent level"""
        try:
            prompt = EXTRACTION_PROMPTS["registration_intent"].format(message=message)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            intent = response.content.lower().strip()
            if intent in ['high', 'medium', 'low', 'none']:
                return intent
            else:
                return self._basic_intent_check(message)
                
        except Exception as e:
            print(f"Error checking registration intent: {e}")
            return self._basic_intent_check(message)
    
    def _basic_intent_check(self, message: str) -> str:
        """Basic fallback intent detection"""
        message_lower = message.lower()
        
        high_intent = ['register', 'sign up', 'create account', 'join now', 'get started']
        medium_intent = ['account', 'personalized', 'customize', 'save preferences', 'track']
        low_intent = ['interested', 'maybe', 'tell me more', 'what do i get']
        
        if any(term in message_lower for term in high_intent):
            return 'high'
        elif any(term in message_lower for term in medium_intent):
            return 'medium'  
        elif any(term in message_lower for term in low_intent):
            return 'low'
        else:
            return 'none'

class ConversationManager:
    def __init__(self):
        self.user_data_cache = {}
    
    def update_user_profile(self, session_id: str, extracted_data: Dict):
        """Update cached user profile with extracted information"""
        if session_id not in self.user_data_cache:
            self.user_data_cache[session_id] = {
                "teams": [],
                "leagues": [],
                "location": "",
                "demographics": "",
                "betting_info": "",
                "registration_signals": []
            }
        
        profile = self.user_data_cache[session_id]
        
        # Merge new data with existing
        if extracted_data.get("teams"):
            profile["teams"].extend([t for t in extracted_data["teams"] if t not in profile["teams"]])
        if extracted_data.get("leagues"):
            profile["leagues"].extend([l for l in extracted_data["leagues"] if l not in profile["leagues"]])
        if extracted_data.get("location") and not profile["location"]:
            profile["location"] = extracted_data["location"]
        if extracted_data.get("demographics"):
            profile["demographics"] = extracted_data["demographics"]
        if extracted_data.get("betting_info"):
            profile["betting_info"] = extracted_data["betting_info"]
    
    def get_user_profile(self, session_id: str) -> Dict:
        """Get current user profile for session"""
        return self.user_data_cache.get(session_id, {})
    
    def should_suggest_registration(self, session_id: str, message_count: int) -> bool:
        """Determine if we should suggest registration based on conversation context"""
        profile = self.get_user_profile(session_id)
        
        # Suggest registration if:
        # - User has shown interest in teams/leagues (has data)
        # - After 3+ meaningful exchanges
        # - User hasn't been asked recently
        
        has_interests = bool(profile.get("teams") or profile.get("leagues"))
        sufficient_messages = message_count >= 3
        
        return has_interests and sufficient_messages

def check_escalation_needed(message: str) -> bool:
    """Check if conversation should be escalated to human agent"""
    message_lower = message.lower()
    
    escalation_triggers = [
        'speak to human', 'human agent', 'representative', 
        'frustrated', 'not working', 'error', 'problem',
        'complaint', 'issue', 'help me', 'transfer',
        'supervisor', 'manager'
    ]
    
    return any(trigger in message_lower for trigger in escalation_triggers)