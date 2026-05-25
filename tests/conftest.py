import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from main import app 
from database import get_session
# import models
from sqlalchemy.pool import StaticPool
from models import Movie, User, UserRating
from auth import get_current_user


##### auth.py, users.py fixtures

# fast in-memory SQLite database for testing
sqlite_url = "sqlite:///:memory:"
engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool 
)

@pytest.fixture(name="session")
def session_fixture():
    """
    Builds all tables before the test starts and 
    destroys all tables after the test finishes
    """
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Overrides the database session dependency to use the test database
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()

##### movies.py, ratings.py, recommendations.py fixtures

@pytest.fixture(name="mock_user")
def mock_user_fixture(session):
    """
    Dummy user in the test DB
    """
    user = User(id=1, email="tester@example.com", hashed_password="pwd", nickname="tester", model_id=42 )
    session.add(user)
    session.commit()
    return user


@pytest.fixture(name="auth_client")
def auth_client_fixture(client, mock_user):
    """
    Test client that automatically bypasses the JWT token check
    """
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)
