from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session, select
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import your DB and Models
from database import get_session
from models import User

# --- CONFIGURATION ---
# SECRET_KEY: In production, generate a real random string and keep it secret!
SECRET_KEY = "super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# This tells FastAPI that routes using this dependency expect a Bearer token
# "tokenUrl" must point to your actual login endpoint (e.g., "/token" or "/auth/token")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# --- UTILITIES ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,  # 1. Sets HTTP Status to 401
    detail="Could not validate credentials",   # 2. The error message sent to the client
    headers={"WWW-Authenticate": "Bearer"},    # 3. Tells the client "I expect a Bearer token"
)

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. CHECK IF TOKEN EXISTS FIRST
    if token is None:
        # We can log this safely because we aren't slicing 'token'
        raise credentials_exception


    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError as e:
        raise credentials_exception

    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    
    if user is None:
        raise credentials_exception
        
    return user