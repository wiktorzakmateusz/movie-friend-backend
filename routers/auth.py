# router for user authentication
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import User, LoginRequest, Token
from security import verify_password
from auth import create_access_token

router = APIRouter(tags=["Auth"])

@router.post("/token", response_model=Token)
def login_for_access_token(
    login_data: LoginRequest, # user email and password
    session: Session = Depends(get_session) # database session
):
    """
    Checks user login and returns a Token model
    """
    
    # finds a user matching the provided email
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()

    # check sif the user was found and
    # if the provided password matches the hashed password in the DB
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # generates a JWT token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}