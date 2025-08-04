from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from database import db

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security instances
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class TokenData:
    def __init__(self, email: str = None, user_id: int = None):
        self.email = email
        self.user_id = user_id


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if email is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(email=email, user_id=user_id)
        return token_data
        
    except JWTError:
        raise credentials_exception


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with email and password"""
    user = db.authenticate_user(email, password)
    if not user:
        return None
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get the current authenticated user from JWT token"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    user = db.retrieve_user_info(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get the current active user (not disabled)"""
    if current_user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


class APIKeyAuth:
    """Simple API key authentication for external services"""
    
    def __init__(self):
        self.valid_api_keys = set(os.getenv("VALID_API_KEYS", "").split(","))
        self.valid_api_keys.discard("")  # Remove empty strings
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify if an API key is valid"""
        return api_key in self.valid_api_keys
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
        """Dependency to verify API key"""
        api_key = credentials.credentials
        
        if not self.verify_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return True


# Create API key authentication instance
api_key_auth = APIKeyAuth()


# Rate limiting placeholder (in production, use Redis or similar)
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.limit = 100  # requests per hour
        self.window = 3600  # 1 hour in seconds
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow().timestamp()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            timestamp for timestamp in self.requests[identifier]
            if now - timestamp < self.window
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.limit:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True


rate_limiter = RateLimiter()


async def check_rate_limit(current_user: Dict[str, Any] = Depends(get_current_user)) -> bool:
    """Rate limiting middleware"""
    identifier = f"user_{current_user['id']}"
    
    if not rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )
    
    return True