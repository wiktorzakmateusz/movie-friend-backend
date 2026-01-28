from typing import List
from fastapi import FastAPI, HTTPException, Depends, status
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware

# Import from our new files
from database import create_db_and_tables, get_session
from models import User, UserCreate, UserRead, LoginRequest, Token
from security import get_password_hash, verify_password 
from auth import create_access_token

app = FastAPI()

origins = [
    "http://localhost:3000",                # For local development
    "https://movie-friend.vercel.app",      # Vercel frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# 1. Sign Up Endpoint
@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Check for existing email
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password & Create DB object
    hashed_pwd = get_password_hash(user.password)
    db_user = User(
        nickname=user.nickname, 
        email=user.email, 
        hashed_password=hashed_pwd
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return db_user

# 2. Get Users Endpoint
@app.get("/users/", response_model=List[UserRead])
def read_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

# 3. Login (Generate Token)
@app.post("/token", response_model=Token)
def login_for_access_token(login_data: LoginRequest, session: Session = Depends(get_session)):
    # 1. Find user by email
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()
    
    # 2. Check if user exists AND password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # 3. Create the token
    # Store the user's email (sub) in the token so it's known who they are later
    access_token = create_access_token(data={"sub": user.email})
    
    # 4. Return the token
    return {"access_token": access_token, "token_type": "bearer"}