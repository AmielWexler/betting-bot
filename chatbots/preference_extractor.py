"""
Preference extraction module for the betting chatbot.
Extracts user preferences like favorite teams, leagues, and risk tolerance from natural language.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExtractedPreferences:
    """Container for extracted user preferences"""
    teams: List[str]
    leagues: List[str]
    risk_tolerance: Optional[str]
    betting_style: Optional[str]
    bet_types: List[str]
    confidence: float


class PreferenceExtractor:
    """Extract user preferences from conversational text"""
    
    def __init__(self):
        # Common football teams (expandable)
        self.team_patterns = {
            # Premier League
            "arsenal", "chelsea", "liverpool", "manchester united", "manchester city", 
            "tottenham", "spurs", "leicester", "west ham", "everton", "aston villa",
            "brighton", "crystal palace", "fulham", "brentford", "nottingham forest",
            "wolves", "bournemouth", "burnley", "sheffield united", "luton",
           
            # La Liga
            "real madrid", "barcelona", "atletico madrid", "sevilla", "valencia", 
            "villarreal", "real sociedad", "athletic bilbao", "betis", "celta vigo",
            
            # Serie A
            "juventus", "ac milan", "inter milan", "napoli", "roma", "lazio", 
            "atalanta", "fiorentina", "torino", "bologna",
            
            # Bundesliga
            "bayern munich", "borussia dortmund", "rb leipzig", "bayer leverkusen",
            "eintracht frankfurt", "wolfsburg", "borussia monchengladbach",
            
            # Ligue 1
            "paris saint-germain", "psg", "marseille", "lyon", "monaco", "lille",
            
            # Other popular teams
            "ajax", "benfica", "porto", "celtic", "rangers"
        }
        
        # League patterns
        self.league_patterns = {
            "premier league": ["premier league", "epl", "english premier league"],
            "la liga": ["la liga", "spanish league", "primera division"],
            "serie a": ["serie a", "italian league"],
            "bundesliga": ["bundesliga", "german league"],
            "ligue 1": ["ligue 1", "french league"],
            "champions league": ["champions league", "ucl", "european cup"],
            "europa league": ["europa league", "uel"],
            "world cup": ["world cup", "fifa world cup"],
            "euros": ["european championship", "euros", "euro 2024"]
        }
        
        # Risk tolerance patterns
        self.risk_patterns = {
            "high": [
                "adrenaline", "adrenilne", "adrenline", "rush", "high risk", "risky", "aggressive", "gamble", 
                "big bet", "all in", "maximum", "extreme", "dangerous", "wild", "fun", "excitement",
                "dont mind losing", "don't mind losing", "losing money", "lose money", "thrill",
                "high stakes", "big stakes", "maximum bet", "go big", "all or nothing"
            ],
            "medium": [
                "moderate", "balanced", "reasonable", "normal", "standard", 
                "medium risk", "careful", "sensible", "reasonable risk"
            ],
            "low": [
                "safe", "conservative", "low risk", "careful", "secure", "minimal", 
                "cautious", "play it safe", "small bet", "safe bet", "low stakes"
            ]
        }
        
        # Betting style patterns
        self.style_patterns = {
            "accumulator": ["accumulator", "acca", "multiple", "combo", "parlay"],
            "single": ["single bet", "straight bet", "individual"],
            "system": ["system bet", "yankee", "patent", "trixie"],
            "live": ["live betting", "in-play", "real-time", "during match"],
            "value": ["value bet", "good odds", "value", "profitable"]
        }
        
        # Bet type patterns
        self.bet_type_patterns = {
            "match_result": ["win", "1x2", "match result", "full time result"],
            "over_under": ["over", "under", "goals", "total goals", "o/u"],
            "both_teams_score": ["both teams score", "btts", "both to score"],
            "handicap": ["handicap", "asian handicap", "spread"],
            "correct_score": ["correct score", "exact score"],
            "first_goalscorer": ["first goalscorer", "anytime goalscorer"],
            "cards": ["cards", "yellow cards", "red cards"],
            "corners": ["corners", "corner kicks"]
        }
    
    def extract_preferences(self, text: str, context: str = "") -> ExtractedPreferences:
        """Extract all preferences from text"""
        text_lower = text.lower()
        full_text = f"{context} {text}".lower() if context else text_lower
        
        teams = self._extract_teams(full_text)
        leagues = self._extract_leagues(full_text)
        risk_tolerance = self._extract_risk_tolerance(full_text)
        betting_style = self._extract_betting_style(full_text)
        bet_types = self._extract_bet_types(full_text)
        
        # Calculate confidence based on matches found
        confidence = self._calculate_confidence(teams, leagues, risk_tolerance, betting_style, bet_types)
        
        return ExtractedPreferences(
            teams=teams,
            leagues=leagues,
            risk_tolerance=risk_tolerance,
            betting_style=betting_style,
            bet_types=bet_types,
            confidence=confidence
        )
    
    def _extract_teams(self, text: str) -> List[str]:
        """Extract team names from text"""
        found_teams = []
        
        for team in self.team_patterns:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(team) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                # Normalize team name
                found_teams.append(self._normalize_team_name(team))
        
        # Additional patterns for common expressions
        # Look for "I love [team]", "betting on [team]", "bets for [team]"
        love_pattern = r'\b(?:love|support|follow|fan of)\s+(\w+)'
        bet_pattern = r'\b(?:bet on|betting on|bets for)\s+(\w+)'
        
        for pattern in [love_pattern, bet_pattern]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                potential_team = match.group(1).lower()
                if potential_team in self.team_patterns:
                    found_teams.append(self._normalize_team_name(potential_team))
        
        return list(set(found_teams))  # Remove duplicates
    
    def _extract_leagues(self, text: str) -> List[str]:
        """Extract league names from text"""
        found_leagues = []
        
        for league_name, patterns in self.league_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    found_leagues.append(league_name)
                    break
        
        return list(set(found_leagues))
    
    def _extract_risk_tolerance(self, text: str) -> Optional[str]:
        """Extract risk tolerance from text"""
        # Check for explicit risk mentions
        for risk_level, patterns in self.risk_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return risk_level
        
        # Enhanced contextual risk inference
        # High risk indicators
        high_risk_context = [
            "big", "high", "maximum", "aggressive", "all in", "for fun", 
            "don't care", "dont care", "lose", "losing", "risk it", "go for it"
        ]
        
        # Low risk indicators  
        low_risk_context = [
            "careful", "safe", "small", "conservative", "secure", "cautious", "minimal"
        ]
        
        # Count matches for each risk level
        high_score = sum(1 for word in high_risk_context if word in text)
        low_score = sum(1 for word in low_risk_context if word in text)
        
        if high_score > low_score and high_score > 0:
            return "high"
        elif low_score > high_score and low_score > 0:
            return "low"
        
        return None
    
    def _extract_betting_style(self, text: str) -> Optional[str]:
        """Extract betting style preferences"""
        for style, patterns in self.style_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return style
        return None
    
    def _extract_bet_types(self, text: str) -> List[str]:
        """Extract preferred bet types"""
        found_types = []
        
        for bet_type, patterns in self.bet_type_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    found_types.append(bet_type)
                    break
        
        return list(set(found_types))
    
    def _normalize_team_name(self, team: str) -> str:
        """Normalize team names to consistent format"""
        # Capitalize properly
        normalized = team.title()
        
        # Handle special cases
        if "psg" in team.lower():
            return "Paris Saint-Germain"
        elif "manchester united" in team.lower():
            return "Manchester United"
        elif "manchester city" in team.lower():
            return "Manchester City"
        elif "real madrid" in team.lower():
            return "Real Madrid"
        elif "atletico madrid" in team.lower():
            return "Atletico Madrid"
        elif "ac milan" in team.lower():
            return "AC Milan"
        elif "inter milan" in team.lower():
            return "Inter Milan"
        elif "bayern munich" in team.lower():
            return "Bayern Munich"
        elif "borussia dortmund" in team.lower():
            return "Borussia Dortmund"
        
        return normalized
    
    def _calculate_confidence(self, teams: List[str], leagues: List[str], 
                            risk_tolerance: Optional[str], betting_style: Optional[str],
                            bet_types: List[str]) -> float:
        """Calculate confidence score for extracted preferences"""
        score = 0.0
        total_possible = 5.0
        
        if teams:
            score += 1.0
        if leagues:
            score += 1.0
        if risk_tolerance:
            score += 1.0
        if betting_style:
            score += 1.0
        if bet_types:
            score += 1.0
        
        return min(score / total_possible, 1.0)
    
    def extract_sentiment_towards_team(self, text: str, team: str) -> Dict[str, any]:
        """Extract sentiment and context about a specific team"""
        text_lower = text.lower()
        team_lower = team.lower()
        
        # Positive indicators
        positive_words = ["love", "fan", "support", "favorite", "best", "great", "amazing", "win"]
        negative_words = ["hate", "dislike", "worst", "terrible", "lose", "bad"]
        
        sentiment = "neutral"
        context_words = []
        
        # Check for team mention with sentiment
        if team_lower in text_lower:
            words_around_team = self._get_words_around_term(text_lower, team_lower, window=5)
            
            if any(word in words_around_team for word in positive_words):
                sentiment = "positive"
            elif any(word in words_around_team for word in negative_words):
                sentiment = "negative"
            
            context_words = words_around_team
        
        return {
            "sentiment": sentiment,
            "context_words": context_words,
            "confidence": 0.8 if sentiment != "neutral" else 0.3
        }
    
    def _get_words_around_term(self, text: str, term: str, window: int = 5) -> List[str]:
        """Get words around a specific term"""
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            if term in word:
                start = max(0, i - window)
                end = min(len(words), i + window + 1)
                result.extend(words[start:end])
        
        return result


# Singleton instance
_preference_extractor = None

def get_preference_extractor() -> PreferenceExtractor:
    """Get the singleton preference extractor instance"""
    global _preference_extractor
    if _preference_extractor is None:
        _preference_extractor = PreferenceExtractor()
    return _preference_extractor


def extract_preferences_from_message(message: str, user_history: str = "") -> Dict:
    """Convenience function to extract preferences from a message"""
    extractor = get_preference_extractor()
    preferences = extractor.extract_preferences(message, user_history)
    
    return {
        "teams": preferences.teams,
        "leagues": preferences.leagues,
        "risk_tolerance": preferences.risk_tolerance,
        "betting_style": preferences.betting_style,
        "bet_types": preferences.bet_types,
        "confidence": preferences.confidence,
        "has_preferences": preferences.confidence > 0.0
    }