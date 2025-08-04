import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import bcrypt
from typing import Optional, Dict, List
import json
from datetime import datetime

class Database:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://betting_user:betting_password@localhost:5433/betting_bot')
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self):
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def retrieve_user_info(self, user_id: int) -> Optional[Dict]:
        with self.get_session() as session:
            result = session.execute(
                text("""
                SELECT u.*, up.favorite_teams, up.favorite_leagues, up.betting_style, up.risk_tolerance
                FROM users u
                LEFT JOIN user_preferences up ON u.id = up.user_id
                WHERE u.id = :user_id AND u.status = 'active'
                """),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return {
                    "id": result.id,
                    "email": result.email,
                    "first_name": result.first_name,
                    "last_name": result.last_name,
                    "age": result.age,
                    "country": result.country,
                    "city": result.city,
                    "language": result.language,
                    "favorite_teams": result.favorite_teams,
                    "favorite_leagues": result.favorite_leagues,
                    "betting_style": result.betting_style,
                    "risk_tolerance": result.risk_tolerance
                }
            return None
    
    def create_user(self, email: str, password: str, first_name: str = None, 
                   last_name: str = None, age: int = None, country: str = None, 
                   city: str = None, language: str = 'en') -> Optional[int]:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        with self.get_session() as session:
            result = session.execute(
                text("""
                INSERT INTO users (email, password_hash, first_name, last_name, age, country, city, language)
                VALUES (:email, :password_hash, :first_name, :last_name, :age, :country, :city, :language)
                RETURNING id
                """),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": age,
                    "country": country,
                    "city": city,
                    "language": language
                }
            ).fetchone()
            
            if result:
                user_id = result.id
                session.execute(
                    text("""
                    INSERT INTO user_preferences (user_id, notification_settings)
                    VALUES (:user_id, :notification_settings)
                    """),
                    {
                        "user_id": user_id,
                        "notification_settings": json.dumps({})
                    }
                )
                return user_id
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        with self.get_session() as session:
            result = session.execute(
                text("""
                SELECT id, email, password_hash, first_name, last_name
                FROM users
                WHERE email = :email AND status = 'active'
                """),
                {"email": email}
            ).fetchone()
            
            if result and bcrypt.checkpw(password.encode('utf-8'), result.password_hash.encode('utf-8')):
                session.execute(
                    text("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :user_id"),
                    {"user_id": result.id}
                )
                
                return {
                    "id": result.id,
                    "email": result.email,
                    "first_name": result.first_name,
                    "last_name": result.last_name
                }
            return None
    
    def create_lead(self, email: str = None, phone: str = None, first_name: str = None,
                   source: str = None, campaign: str = None, utm_source: str = None,
                   utm_medium: str = None, utm_campaign: str = None) -> Optional[int]:
        with self.get_session() as session:
            result = session.execute(
                text("""
                INSERT INTO leads (email, phone, first_name, source, campaign, utm_source, utm_medium, utm_campaign)
                VALUES (:email, :phone, :first_name, :source, :campaign, :utm_source, :utm_medium, :utm_campaign)
                RETURNING id
                """),
                {
                    "email": email,
                    "phone": phone,
                    "first_name": first_name,
                    "source": source,
                    "campaign": campaign,
                    "utm_source": utm_source,
                    "utm_medium": utm_medium,
                    "utm_campaign": utm_campaign
                }
            ).fetchone()
            
            return result.id if result else None
    
    def create_chat_session(self, user_id: int = None, lead_id: int = None, 
                           session_type: str = 'conversion') -> Optional[int]:
        with self.get_session() as session:
            result = session.execute(
                text("""
                INSERT INTO chat_sessions (user_id, lead_id, session_type)
                VALUES (:user_id, :lead_id, :session_type)
                RETURNING id
                """),
                {
                    "user_id": user_id,
                    "lead_id": lead_id,
                    "session_type": session_type
                }
            ).fetchone()
            
            return result.id if result else None
    
    def add_chat_message(self, session_id: int, message: str, sender: str, 
                        message_type: str = 'text', metadata: Dict = None) -> bool:
        with self.get_session() as session:
            session.execute(
                text("""
                INSERT INTO chat_messages (session_id, message, sender, message_type, metadata)
                VALUES (:session_id, :message, :sender, :message_type, :metadata)
                """),
                {
                    "session_id": session_id,
                    "message": message,
                    "sender": sender,
                    "message_type": message_type,
                    "metadata": json.dumps(metadata) if metadata else None
                }
            )
            return True
    
    def get_chat_history(self, session_id: int) -> List[Dict]:
        with self.get_session() as session:
            results = session.execute(
                text("""
                SELECT message, sender, timestamp, message_type, metadata
                FROM chat_messages
                WHERE session_id = :session_id
                ORDER BY timestamp ASC
                """),
                {"session_id": session_id}
            ).fetchall()
            
            return [
                {
                    "message": result.message,
                    "sender": result.sender,
                    "timestamp": result.timestamp,
                    "message_type": result.message_type,
                    "metadata": json.loads(result.metadata) if result.metadata else None
                }
                for result in results
            ]

    def check_register_intent(self, message: str) -> bool:
        register_keywords = ['register', 'sign up', 'create account', 'join', 'signup']
        return any(keyword in message.lower() for keyword in register_keywords)
    
    def store_conversation_data(self, session_id: int, user_profile: Dict) -> bool:
        """Store extracted user data from conversation"""
        with self.get_session() as session:
            try:
                # Store as metadata in chat_messages or create a separate conversation_data table
                session.execute(
                    text("""
                    INSERT INTO chat_messages (session_id, message, sender, message_type, metadata)
                    VALUES (:session_id, 'User profile update', 'system', 'profile_update', :metadata)
                    """),
                    {
                        "session_id": session_id,
                        "metadata": json.dumps(user_profile)
                    }
                )
                return True
            except Exception as e:
                print(f"Error storing conversation data: {e}")
                return False
    
    def update_lead_interests(self, lead_id: int, interests: Dict) -> bool:
        """Update lead with extracted interests and demographics"""
        with self.get_session() as session:
            try:
                # Update leads table with extracted information
                update_data = {}
                if interests.get("location"):
                    update_data["source"] = interests["location"]
                
                # Store detailed interests in a JSON field (we'll need to add this column)
                metadata = {
                    "favorite_teams": interests.get("teams", []),
                    "favorite_leagues": interests.get("leagues", []),
                    "demographics": interests.get("demographics", ""),
                    "betting_info": interests.get("betting_info", "")
                }
                
                session.execute(
                    text("""
                    UPDATE leads 
                    SET updated_at = CURRENT_TIMESTAMP,
                        campaign = :metadata
                    WHERE id = :lead_id
                    """),
                    {
                        "lead_id": lead_id,
                        "metadata": json.dumps(metadata)
                    }
                )
                return True
            except Exception as e:
                print(f"Error updating lead interests: {e}")
                return False
    
    def get_conversation_profile(self, session_id: int) -> Optional[Dict]:
        """Retrieve accumulated user profile from conversation"""
        with self.get_session() as session:
            try:
                results = session.execute(
                    text("""
                    SELECT metadata
                    FROM chat_messages
                    WHERE session_id = :session_id 
                    AND message_type = 'profile_update'
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """),
                    {"session_id": session_id}
                ).fetchone()
                
                if results and results.metadata:
                    return json.loads(results.metadata)
                return None
            except Exception as e:
                print(f"Error getting conversation profile: {e}")
                return None

    def ensure_user_exists(self, user_id: int) -> bool:
        """Ensure a user exists, create test user if needed"""
        with self.get_session() as session:
            try:
                # Check if user exists
                user_exists = session.execute(
                    text("SELECT id FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                
                if not user_exists:
                    print(f"🔧 Creating test user {user_id} for preference storage")
                    # Create a test user
                    session.execute(
                        text("""
                        INSERT INTO users (id, email, password_hash, first_name, status)
                        VALUES (:user_id, :email, :password_hash, :first_name, 'active')
                        ON CONFLICT (id) DO NOTHING
                        """),
                        {
                            "user_id": user_id,
                            "email": f"test_user_{user_id}@example.com",
                            "password_hash": "test_hash",
                            "first_name": f"TestUser{user_id}"
                        }
                    )
                    print(f"✅ Created test user {user_id}")
                
                return True
            except Exception as e:
                print(f"❌ Error ensuring user exists: {e}")
                return False

    def update_user_preferences(self, user_id: int, favorite_teams: List[str] = None, 
                               favorite_leagues: List[str] = None, betting_style: str = None,
                               risk_tolerance: str = None) -> bool:
        """Update user preferences based on extracted data from conversations"""
        
        # First ensure the user exists
        if not self.ensure_user_exists(user_id):
            print(f"❌ Cannot update preferences: user {user_id} creation failed")
            return False
            
        with self.get_session() as session:
            try:
                print(f"🔍 Updating preferences for user {user_id}: teams={favorite_teams}, risk={risk_tolerance}")
                
                # Check if user preferences exist
                existing = session.execute(
                    text("SELECT id FROM user_preferences WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                
                if existing:
                    # Update existing preferences
                    update_fields = []
                    params = {"user_id": user_id}
                    
                    if favorite_teams is not None:
                        # Merge with existing teams to avoid duplicates
                        current_teams = session.execute(
                            text("SELECT favorite_teams FROM user_preferences WHERE user_id = :user_id"),
                            {"user_id": user_id}
                        ).fetchone()
                        
                        existing_teams = current_teams.favorite_teams if current_teams and current_teams.favorite_teams else []
                        merged_teams = list(set(existing_teams + favorite_teams))
                        update_fields.append("favorite_teams = :favorite_teams")
                        # Convert Python list to PostgreSQL array format
                        params["favorite_teams"] = merged_teams
                        print(f"🔧 Merging teams: existing={existing_teams}, new={favorite_teams}, merged={merged_teams}")
                    
                    if favorite_leagues is not None:
                        # Merge with existing leagues
                        current_leagues = session.execute(
                            text("SELECT favorite_leagues FROM user_preferences WHERE user_id = :user_id"),
                            {"user_id": user_id}
                        ).fetchone()
                        
                        existing_leagues = current_leagues.favorite_leagues if current_leagues and current_leagues.favorite_leagues else []
                        merged_leagues = list(set(existing_leagues + favorite_leagues))
                        update_fields.append("favorite_leagues = :favorite_leagues")
                        params["favorite_leagues"] = merged_leagues
                        print(f"🔧 Merging leagues: existing={existing_leagues}, new={favorite_leagues}, merged={merged_leagues}")
                    
                    if betting_style is not None:
                        update_fields.append("betting_style = :betting_style")
                        params["betting_style"] = betting_style
                    
                    if risk_tolerance is not None:
                        update_fields.append("risk_tolerance = :risk_tolerance")
                        params["risk_tolerance"] = risk_tolerance
                    
                    if update_fields:
                        query = f"UPDATE user_preferences SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = :user_id"
                        print(f"🔍 Executing SQL: {query}")
                        print(f"🔍 With parameters: {params}")
                        session.execute(text(query), params)
                        print(f"✅ UPDATE executed successfully")
                else:
                    # Create new preferences record
                    insert_params = {
                        "user_id": user_id,
                        "favorite_teams": favorite_teams or [],
                        "favorite_leagues": favorite_leagues or [],
                        "betting_style": betting_style,
                        "risk_tolerance": risk_tolerance
                    }
                    print(f"🔍 Creating new preferences record")
                    print(f"🔍 INSERT parameters: {insert_params}")
                    
                    session.execute(
                        text("""
                        INSERT INTO user_preferences (user_id, favorite_teams, favorite_leagues, betting_style, risk_tolerance)
                        VALUES (:user_id, :favorite_teams, :favorite_leagues, :betting_style, :risk_tolerance)
                        """),
                        insert_params
                    )
                    print(f"✅ INSERT executed successfully")
                
                # Verify the update worked
                verification = session.execute(
                    text("SELECT favorite_teams, favorite_leagues, risk_tolerance FROM user_preferences WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                
                if verification:
                    print(f"✅ Preferences saved successfully for user {user_id}")
                    print(f"📝 Stored: teams={verification.favorite_teams}, risk={verification.risk_tolerance}")
                    return True
                else:
                    print(f"❌ Verification failed: preferences not found after save")
                    return False
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ Database error updating user preferences for user {user_id}:")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                print(f"   Full traceback:\n{error_details}")
                return False

    def get_user_preferences(self, user_id: int) -> Optional[Dict]:
        """Get user preferences including betting preferences"""
        with self.get_session() as session:
            try:
                result = session.execute(
                    text("""
                    SELECT up.favorite_teams, up.favorite_leagues, up.betting_style, up.risk_tolerance,
                           ubp.preferred_markets, ubp.max_stake_per_bet, ubp.bankroll_size, 
                           ubp.favorite_bet_types, ubp.blacklisted_teams
                    FROM user_preferences up
                    LEFT JOIN user_betting_preferences ubp ON up.user_id = ubp.user_id
                    WHERE up.user_id = :user_id
                    """),
                    {"user_id": user_id}
                ).fetchone()
                
                if result:
                    return {
                        "favorite_teams": result.favorite_teams or [],
                        "favorite_leagues": result.favorite_leagues or [],
                        "betting_style": result.betting_style,
                        "risk_tolerance": result.risk_tolerance,
                        "preferred_markets": result.preferred_markets or [],
                        "max_stake_per_bet": float(result.max_stake_per_bet) if result.max_stake_per_bet else None,
                        "bankroll_size": float(result.bankroll_size) if result.bankroll_size else None,
                        "favorite_bet_types": result.favorite_bet_types or [],
                        "blacklisted_teams": result.blacklisted_teams or []
                    }
                return None
            except Exception as e:
                print(f"Error getting user preferences: {e}")
                return None

    def update_betting_preferences(self, user_id: int, preferred_markets: List[str] = None,
                                  max_stake_per_bet: float = None, bankroll_size: float = None,
                                  favorite_bet_types: List[str] = None, risk_tolerance: str = None) -> bool:
        """Update user betting preferences"""
        with self.get_session() as session:
            try:
                # Check if betting preferences exist
                existing = session.execute(
                    text("SELECT id FROM user_betting_preferences WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                
                if existing:
                    # Update existing preferences
                    update_fields = []
                    params = {"user_id": user_id}
                    
                    if preferred_markets is not None:
                        update_fields.append("preferred_markets = :preferred_markets")
                        params["preferred_markets"] = preferred_markets
                    
                    if max_stake_per_bet is not None:
                        update_fields.append("max_stake_per_bet = :max_stake_per_bet")
                        params["max_stake_per_bet"] = max_stake_per_bet
                    
                    if bankroll_size is not None:
                        update_fields.append("bankroll_size = :bankroll_size")
                        params["bankroll_size"] = bankroll_size
                    
                    if favorite_bet_types is not None:
                        update_fields.append("favorite_bet_types = :favorite_bet_types")
                        params["favorite_bet_types"] = favorite_bet_types
                    
                    if risk_tolerance is not None:
                        update_fields.append("risk_tolerance = :risk_tolerance")
                        params["risk_tolerance"] = risk_tolerance
                    
                    if update_fields:
                        query = f"UPDATE user_betting_preferences SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = :user_id"
                        session.execute(text(query), params)
                else:
                    # Create new betting preferences record
                    session.execute(
                        text("""
                        INSERT INTO user_betting_preferences (user_id, preferred_markets, max_stake_per_bet, 
                                                              bankroll_size, favorite_bet_types, risk_tolerance)
                        VALUES (:user_id, :preferred_markets, :max_stake_per_bet, :bankroll_size, 
                                :favorite_bet_types, :risk_tolerance)
                        """),
                        {
                            "user_id": user_id,
                            "preferred_markets": preferred_markets or [],
                            "max_stake_per_bet": max_stake_per_bet,
                            "bankroll_size": bankroll_size,
                            "favorite_bet_types": favorite_bet_types or [],
                            "risk_tolerance": risk_tolerance or "medium"
                        }
                    )
                
                return True
            except Exception as e:
                print(f"Error updating betting preferences: {e}")
                return False

db = Database()