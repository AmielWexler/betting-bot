#!/usr/bin/env python3
"""
Test script for database preference storage functionality.
This tests the complete flow from preference extraction to database storage.
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbots.preference_extractor import extract_preferences_from_message
from database import db


def test_database_connection():
    """Test basic database connectivity"""
    print("=== Testing Database Connection ===")
    
    try:
        if db.test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def test_user_creation():
    """Test user creation functionality"""
    print("\n=== Testing User Creation ===")
    
    test_user_id = 12345
    
    try:
        success = db.ensure_user_exists(test_user_id)
        if success:
            print(f"✅ User {test_user_id} creation/verification successful")
            return test_user_id
        else:
            print(f"❌ User {test_user_id} creation failed")
            return None
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return None


def test_preference_extraction_and_storage():
    """Test the complete flow from message to database"""
    print("\n=== Testing Complete Preference Flow ===")
    
    # Create test user
    test_user_id = 12345
    if not db.ensure_user_exists(test_user_id):
        print("❌ Cannot proceed: user creation failed")
        return False
    
    # Test messages with expected outcomes
    test_cases = [
        {
            "message": "I love Arsenal, give me some interesting bets for their next games, I like the adrenaline from the risk. don't mind losing a bit of money for fun.",
            "expected_teams": ["Arsenal"],
            "expected_risk": "high",
            "description": "User's original prompt"
        },
        {
            "message": "I also follow Chelsea and prefer safe betting strategies",
            "expected_teams": ["Chelsea"],
            "expected_risk": "low",
            "description": "Additional team + low risk"
        },
        {
            "message": "I love watching Premier League matches",
            "expected_leagues": ["premier league"],
            "description": "League preference"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        print(f"Message: '{test_case['message']}'")
        
        # Step 1: Extract preferences
        extracted = extract_preferences_from_message(test_case['message'])
        print(f"📊 Extracted: {extracted}")
        
        # Step 2: Store preferences if found
        if extracted['has_preferences'] and extracted['confidence'] > 0.1:
            print(f"💾 Attempting to store preferences...")
            
            success = db.update_user_preferences(
                user_id=test_user_id,
                favorite_teams=extracted['teams'] if extracted['teams'] else None,
                favorite_leagues=extracted['leagues'] if extracted['leagues'] else None,
                risk_tolerance=extracted['risk_tolerance'],
                betting_style=extracted['betting_style']
            )
            
            if success:
                print(f"✅ Preferences stored successfully")
                
                # Step 3: Verify storage by reading back
                stored_prefs = db.get_user_preferences(test_user_id)
                if stored_prefs:
                    print(f"📖 Retrieved from DB: {stored_prefs}")
                    
                    # Verify expected data is present
                    if "expected_teams" in test_case:
                        for expected_team in test_case["expected_teams"]:
                            if expected_team in stored_prefs.get("favorite_teams", []):
                                print(f"✅ Team '{expected_team}' found in database")
                            else:
                                print(f"❌ Team '{expected_team}' NOT found in database")
                    
                    if "expected_risk" in test_case:
                        if stored_prefs.get("risk_tolerance") == test_case["expected_risk"]:
                            print(f"✅ Risk tolerance '{test_case['expected_risk']}' matches")
                        else:
                            print(f"❌ Risk tolerance mismatch: expected '{test_case['expected_risk']}', got '{stored_prefs.get('risk_tolerance')}'")
                    
                    if "expected_leagues" in test_case:
                        for expected_league in test_case["expected_leagues"]:
                            if expected_league in stored_prefs.get("favorite_leagues", []):
                                print(f"✅ League '{expected_league}' found in database")
                            else:
                                print(f"❌ League '{expected_league}' NOT found in database")
                
                else:
                    print(f"❌ Could not retrieve stored preferences")
            else:
                print(f"❌ Failed to store preferences")
        else:
            print(f"⏭️ Skipped storage (confidence: {extracted['confidence']:.2f})")
        
        print("-" * 60)
    
    return True


def test_array_handling():
    """Test PostgreSQL array handling specifically"""
    print("\n=== Testing PostgreSQL Array Handling ===")
    
    test_user_id = 12346
    
    # Ensure test user exists
    if not db.ensure_user_exists(test_user_id):
        print("❌ Cannot proceed: user creation failed")
        return False
    
    # Test with multiple teams and leagues
    test_teams = ["Arsenal", "Chelsea", "Liverpool"]
    test_leagues = ["premier league", "champions league"]
    
    print(f"Testing arrays: teams={test_teams}, leagues={test_leagues}")
    
    success = db.update_user_preferences(
        user_id=test_user_id,
        favorite_teams=test_teams,
        favorite_leagues=test_leagues,
        risk_tolerance="medium"
    )
    
    if success:
        print("✅ Array storage successful")
        
        # Verify retrieval
        stored = db.get_user_preferences(test_user_id)
        if stored:
            print(f"Retrieved teams: {stored.get('favorite_teams')}")
            print(f"Retrieved leagues: {stored.get('favorite_leagues')}")
            
            # Check all teams are present
            stored_teams = stored.get('favorite_teams', [])
            all_teams_present = all(team in stored_teams for team in test_teams)
            
            if all_teams_present:
                print("✅ All teams stored and retrieved correctly")
            else:
                print(f"❌ Team mismatch: expected {test_teams}, got {stored_teams}")
            
            # Check all leagues are present
            stored_leagues = stored.get('favorite_leagues', [])
            all_leagues_present = all(league in stored_leagues for league in test_leagues)
            
            if all_leagues_present:
                print("✅ All leagues stored and retrieved correctly")
            else:
                print(f"❌ League mismatch: expected {test_leagues}, got {stored_leagues}")
        else:
            print("❌ Could not retrieve stored preferences")
    else:
        print("❌ Array storage failed")


def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    
    test_user_ids = [12345, 12346]
    
    for user_id in test_user_ids:
        try:
            with db.get_session() as session:
                from sqlalchemy import text
                # Remove preferences
                session.execute(
                    text("DELETE FROM user_preferences WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                # Remove test users
                session.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                print(f"🧹 Cleaned up test user {user_id}")
        except Exception as e:
            print(f"⚠️ Error cleaning up user {user_id}: {e}")


if __name__ == "__main__":
    print("Database Preference Storage Test Suite")
    print("=" * 50)
    
    try:
        # Run tests
        if not test_database_connection():
            print("\n❌ Cannot proceed without database connection")
            sys.exit(1)
        
        test_user_creation()
        test_preference_extraction_and_storage()
        test_array_handling()
        
        print("\n" + "=" * 50)
        print("✅ Test suite completed!")
        
        # Ask if user wants to clean up
        cleanup_response = input("\nDo you want to clean up test data? (y/n): ")
        if cleanup_response.lower() in ['y', 'yes']:
            cleanup_test_data()
        else:
            print("Test data left in database for inspection")
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()