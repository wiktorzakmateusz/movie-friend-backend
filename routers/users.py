# router for handling users in the db
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import User, UserCreate, UserRead
from security import get_password_hash

# router setup with prefix for all user-related endpoints
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserRead)
def create_user(
    user: UserCreate, 
    session: Session = Depends(get_session)
):
    """
    Registers a new user in the database
    """

    # check if a user with this email already exists
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # securely hashes the plaintext password before saving
    hashed_pwd = get_password_hash(user.password)

    # creates the database model instance
    db_user = User(nickname=user.nickname, email=user.email, hashed_password=hashed_pwd)

    # saves to database
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# TO DELETE
# @router.get("/", response_model=List[UserRead])
# def read_users(session: Session = Depends(get_session)):
#     """
#     Retrieves a list of all registered users
#     """
#     # executes a basic select query to fetch all users
#     return session.exec(select(User)).all()