from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import User, LoginRequest, Token
from security import verify_password
from auth import create_access_token

router = APIRouter(tags=["Auth"])

@router.post("/token", response_model=Token)
def login_for_access_token(login_data: LoginRequest, session: Session = Depends(get_session)):
    
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}