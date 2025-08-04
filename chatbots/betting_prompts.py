"""
Specialized prompts for the football betting chatbot
"""

BETTING_SYSTEM_PROMPT = """You are an expert football betting assistant with deep knowledge of football analysis, betting strategies, and risk management. Your role is to provide intelligent, data-driven insights to help users make informed betting decisions.

CORE CAPABILITIES:
- Analyze team form, player statistics, and match dynamics
- Provide betting strategy recommendations based on data
- Explain market movements and betting value opportunities
- Offer risk management advice and bankroll management tips
- Answer questions about football leagues, teams, and players

PERSONALITY & TONE:
- Professional but approachable
- Data-driven and analytical
- Honest about uncertainties and risks
- Educational and informative
- Never overly confident or guarantee wins

BETTING PRINCIPLES TO FOLLOW:
1. Always emphasize responsible gambling
2. Focus on value betting over sure wins
3. Recommend proper bankroll management (1-3% per bet)
4. Explain the reasoning behind suggestions
5. Mention when information is incomplete or uncertain
6. Encourage long-term thinking over quick wins

RISK WARNINGS TO INCLUDE:
- Betting involves risk and potential loss
- Past performance doesn't guarantee future results
- Never bet more than you can afford to lose
- Consider the entertainment value of betting

RESPONSE STRUCTURE:
1. Direct answer to the user's question
2. Supporting analysis with relevant data
3. Risk assessment and bankroll considerations
4. Additional insights or related information
5. Responsible gambling reminder when appropriate

When you don't have specific information, acknowledge this limitation and suggest general principles or alternatives."""

BETTING_CONVERSATION_TEMPLATES = {
    "welcome_back": """Welcome back! I'm your football betting assistant. I can help you with:

🔍 **Match Analysis**: Team form, head-to-head records, key player availability
📊 **Betting Strategies**: Value betting, market analysis, risk management  
⚽ **Football Insights**: League standings, player statistics, tactical analysis
💰 **Bankroll Management**: Staking plans, risk assessment, long-term profitability

What would you like to analyze today?""",

    "team_analysis_template": """Based on the available data, here's my analysis of {team_name}:

**Recent Form**: {recent_form}
**Key Strengths**: {strengths}
**Areas of Concern**: {weaknesses}
**Betting Considerations**: {betting_notes}

**Risk Assessment**: {risk_level}
Remember to only bet what you can afford to lose and consider this as one factor in your decision-making process.""",

    "match_prediction_template": """**{home_team} vs {away_team} Analysis**

**Key Factors**:
{key_factors}

**Betting Opportunities**:
{betting_opportunities}

**Risk Assessment**: {risk_level}
**Recommended Stake**: {stake_recommendation}

*Remember: This analysis is based on available data and football can be unpredictable. Always gamble responsibly.*""",

    "value_bet_explanation": """🎯 **Value Betting Opportunity Identified**

**The Situation**: {situation}
**Market Odds**: {market_odds}
**Fair Value Estimate**: {fair_value}
**Potential Value**: {value_percentage}

**Why This Might Be Value**:
{reasoning}

**Risk Factors to Consider**:
{risk_factors}

**Recommendation**: {recommendation}

*Value betting is about long-term profitability. Individual bets can still lose even when they represent good value.*""",

    "bankroll_management": """💰 **Bankroll Management Principles**

Based on your question about staking, here are key principles:

**The 1-3% Rule**: Never risk more than 1-3% of your total bankroll on a single bet
**Unit System**: Define 1 unit = 1% of bankroll, bet 1-3 units based on confidence
**Bankroll Tracking**: Keep detailed records of all bets and results
**Emotional Control**: Stick to your system regardless of recent wins/losses

**For Your Situation**: {personalized_advice}""",

    "no_data_response": """I don't have specific data about that particular {query_type} right now. However, I can offer some general guidance:

{general_advice}

For the most current information, I'd recommend checking:
- Official team websites and social media
- Recent match reports and news
- Live betting markets for real-time insights

Would you like me to help you analyze this from a different angle or discuss general principles for {query_type}?""",

    "responsible_gambling": """🛡️ **Responsible Gambling Guidelines**

Remember these important principles:
- Set a budget and stick to it
- Never chase losses with bigger bets
- Take regular breaks from betting
- Don't bet when emotional or under pressure
- Consider betting as entertainment, not income
- Seek help if gambling becomes problematic

**Support Resources**:
- Gamblers Anonymous
- National Problem Gambling Helpline
- Self-exclusion tools on betting sites""",

    "market_movement": """📈 **Market Movement Analysis**

**Odds Movement Detected**: {movement_description}
**Possible Reasons**: {reasons}
**Market Sentiment**: {sentiment}

**Betting Implications**:
{implications}

**Action Considerations**:
{recommendations}

*Market movements can indicate smart money or public sentiment. Always consider multiple factors before betting.*""",

    "injury_impact": """🏥 **Injury Impact Assessment**

**Player**: {player_name}
**Injury Status**: {injury_status}
**Team Impact**: {team_impact}

**Betting Considerations**:
{betting_impact}

**Market Reaction**: {market_reaction}

*Player availability can significantly impact match outcomes. Always check team news close to kickoff.*""",

    "error_response": """I apologize, but I'm having difficulty processing your request right now. This might be due to:

- Temporary technical issues
- Incomplete data for your specific query
- Need for more context about your question

Could you please:
1. Rephrase your question with more details
2. Try a different type of analysis
3. Ask about general betting principles instead

I'm here to help with football betting analysis, team insights, and strategy discussions!"""
}

def get_personalized_prompt(user_profile: dict, query_context: str) -> str:
    """Generate a personalized prompt based on user profile and query context"""
    
    base_prompt = BETTING_SYSTEM_PROMPT
    
    # Add user context
    user_context = "\n\nUSER CONTEXT:\n"
    
    if user_profile.get("favorite_teams"):
        user_context += f"- Favorite teams: {', '.join(user_profile['favorite_teams'])}\n"
    
    if user_profile.get("favorite_leagues"):
        user_context += f"- Follows leagues: {', '.join(user_profile['favorite_leagues'])}\n"
    
    if user_profile.get("betting_style"):
        user_context += f"- Betting style: {user_profile['betting_style']}\n"
    
    if user_profile.get("risk_tolerance"):
        user_context += f"- Risk tolerance: {user_profile['risk_tolerance']}\n"
    
    if user_profile.get("language") and user_profile["language"] != "en":
        user_context += f"- Preferred language: {user_profile['language']}\n"
    
    # Add query context
    if query_context:
        user_context += f"\nCURRENT QUERY CONTEXT:\n{query_context}\n"
    
    # Add personalization instructions
    personalization = """
PERSONALIZATION INSTRUCTIONS:
- Reference user's favorite teams when relevant
- Adapt recommendations to their betting style and risk tolerance
- Use examples from their preferred leagues when possible
- Maintain their language preference
- Build on previous conversation context
"""
    
    return base_prompt + user_context + personalization

def format_response_with_context(template_key: str, context: dict) -> str:
    """Format a response template with the provided context"""
    
    if template_key not in BETTING_CONVERSATION_TEMPLATES:
        return BETTING_CONVERSATION_TEMPLATES["error_response"]
    
    template = BETTING_CONVERSATION_TEMPLATES[template_key]
    
    try:
        return template.format(**context)
    except KeyError as e:
        return f"Template formatting error: Missing context key {e}. Please provide all required information."
    except Exception as e:
        return BETTING_CONVERSATION_TEMPLATES["error_response"]

def get_query_category(query: str) -> str:
    """Categorize user query to determine appropriate response type"""
    
    query_lower = query.lower()
    
    # Team-related queries
    team_keywords = ["team", "form", "performance", "squad", "players", "manager", "tactics"]
    if any(keyword in query_lower for keyword in team_keywords):
        return "team_analysis"
    
    # Match prediction queries
    match_keywords = ["vs", "match", "game", "fixture", "prediction", "who will win", "score"]
    if any(keyword in query_lower for keyword in match_keywords):
        return "match_prediction"
    
    # Betting strategy queries
    strategy_keywords = ["bet", "odds", "value", "strategy", "bankroll", "stake", "profitable"]
    if any(keyword in query_lower for keyword in strategy_keywords):
        return "betting_strategy"
    
    # Player-related queries
    player_keywords = ["player", "injury", "suspension", "transfer", "goals", "assists"]
    if any(keyword in query_lower for keyword in player_keywords):
        return "player_analysis"
    
    # League/competition queries
    league_keywords = ["league", "table", "standings", "championship", "premier league", "champions league"]
    if any(keyword in query_lower for keyword in league_keywords):
        return "league_analysis"
    
    # Market/odds queries
    market_keywords = ["market", "odds", "bookmaker", "price", "movement", "value bet"]
    if any(keyword in query_lower for keyword in market_keywords):
        return "market_analysis"
    
    return "general"