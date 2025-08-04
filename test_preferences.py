#!/usr/bin/env python3
"""
Test script for user preference extraction and storage functionality.
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbots.preference_extractor import extract_preferences_from_message, get_preference_extractor


def test_preference_extraction():
    """Test the preference extraction functionality"""
    print("=== Testing Preference Extraction ===\n")
    
    # Test cases
    test_cases = [
        {
            "message": "I want to bet on Arsenal for adrenaline rush risk",
            "expected": {
                "teams": ["Arsenal"],
                "risk_tolerance": "high",
                "description": "Basic team + high risk extraction"
            }
        },
        {
            "message": "I love Liverpool and Manchester United, prefer safe betting",
            "expected": {
                "teams": ["Liverpool", "Manchester United"],
                "risk_tolerance": "low",
                "description": "Multiple teams + low risk"
            }
        },
        {
            "message": "I follow Premier League and La Liga closely",
            "expected": {
                "leagues": ["premier league", "la liga"],
                "description": "League preferences"
            }
        },
        {
            "message": "I prefer over/under bets and both teams to score",
            "expected": {
                "bet_types": ["over_under", "both_teams_score"],
                "description": "Bet type preferences"
            }
        },
        {
            "message": "Real Madrid vs Barcelona tonight, going for high stakes accumulator",
            "expected": {
                "teams": ["Real Madrid", "Barcelona"],
                "betting_style": "accumulator",
                "risk_tolerance": "high",
                "description": "Complex extraction with multiple elements"
            }
        }
    ]
    
    extractor = get_preference_extractor()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['expected']['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Extract preferences
        extracted = extract_preferences_from_message(test_case['message'])
        
        print(f"Results:")
        print(f"  Teams: {extracted['teams']}")
        print(f"  Leagues: {extracted['leagues']}")
        print(f"  Risk: {extracted['risk_tolerance']}")
        print(f"  Style: {extracted['betting_style']}")
        print(f"  Bet Types: {extracted['bet_types']}")
        print(f"  Confidence: {extracted['confidence']:.2f}")
        
        # Simple validation
        success = True
        if "teams" in test_case["expected"]:
            if not all(team in extracted['teams'] for team in test_case["expected"]["teams"]):
                success = False
                print(f"  ❌ Expected teams {test_case['expected']['teams']}, got {extracted['teams']}")
        
        if "risk_tolerance" in test_case["expected"]:
            if extracted['risk_tolerance'] != test_case["expected"]["risk_tolerance"]:
                success = False
                print(f"  ❌ Expected risk {test_case['expected']['risk_tolerance']}, got {extracted['risk_tolerance']}")
        
        if success:
            print(f"  ✅ Test passed")
        
        print("-" * 50)


def test_database_integration():
    """Test the database integration (requires running database)"""
    print("\n=== Testing Database Integration ===\n")
    
    try:
        from database import db
        
        # Test database connection
        if not db.test_connection():
            print("❌ Database connection failed. Make sure PostgreSQL is running.")
            return
        
        print("✅ Database connection successful")
        
        # Test user preference updates
        test_user_id = 999  # Test user ID
        
        # Test updating preferences
        success = db.update_user_preferences(
            user_id=test_user_id,
            favorite_teams=["Arsenal", "Liverpool"],
            favorite_leagues=["premier league"],
            risk_tolerance="high",
            betting_style="aggressive"
        )
        
        if success:
            print("✅ Successfully updated user preferences")
            
            # Test retrieving preferences
            preferences = db.get_user_preferences(test_user_id)
            if preferences:
                print(f"✅ Retrieved preferences: {preferences}")
            else:
                print("❌ Failed to retrieve preferences")
        else:
            print("❌ Failed to update user preferences")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print("This is expected if the database is not running.")


def test_full_integration():
    """Test the full integration with a realistic conversation"""
    print("\n=== Testing Full Integration ===\n")
    
    test_messages = [
        "Hi, I'm interested in betting on football",
        "I want to bet on Arsenal for adrenaline rush risk",
        "I also follow Chelsea and prefer Premier League matches",
        "What are the odds for Arsenal vs Chelsea?"
    ]
    
    print("Simulating a conversation with preference extraction:")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\nMessage {i}: '{message}'")
        
        extracted = extract_preferences_from_message(message)
        
        if extracted['has_preferences']:
            print(f"  Extracted preferences:")
            print(f"    Teams: {extracted['teams']}")
            print(f"    Leagues: {extracted['leagues']}")
            print(f"    Risk: {extracted['risk_tolerance']}")
            print(f"    Confidence: {extracted['confidence']:.2f}")
        else:
            print("  No preferences extracted")


if __name__ == "__main__":
    print("User Preference Extraction Test Suite")
    print("=" * 50)
    
    test_preference_extraction()
    test_database_integration()
    test_full_integration()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")