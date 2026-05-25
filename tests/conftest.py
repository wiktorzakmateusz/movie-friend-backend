import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from main import app 
from database import get_session
import models
from sqlalchemy.pool import StaticPool

# fast in-memory SQLite database for testing
sqlite_url = "sqlite:///:memory:"
engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool 
)

@pytest.fixture(name="session")
def session_fixture():
    # builds all tables before the test starts
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # destroys all tables after the test finishes
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    # using test database
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    
    yield client
    
    # cleans up the override after the test
    app.dependency_overrides.clear()