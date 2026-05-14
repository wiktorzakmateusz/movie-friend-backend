# authentication handling
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session, select

from database import get_session
from models import User

# TODO: CHANGE SECRET KEY
SECRET_KEY = "super-secret-key-change-this-in-production"
ALGORITHM = "HS256" # cryptographic algorithm used to sign the token
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # how long the token remains valid

# OAuth2 scheme - looks for a token in the "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Generates a new JSON Web Token (JWT) containing the provided data payload
    """
    to_encode = data.copy()

    # determines the expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # encodes the payload into a signed JWT string using the secret key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# helper for unauthorized exception
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,  
    detail="Could not validate credentials",  
    headers={"WWW-Authenticate": "Bearer"},    
)

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    """
    FastAPI Dependency that extracts the JWT from the request, decodes it, 
    and fetches the corresponding user from the database
    """
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # check if the token was provided in the header
    if token is None:
        raise credentials_exception

    try:
        # decodes the token using the secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError as e:
        raise credentials_exception

    # queries the database to ensure the user still exists
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    
    if user is None:
        raise credentials_exception
        
    return user