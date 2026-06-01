import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from main import app 
from database import get_session
import numpy as np
from sqlalchemy.pool import StaticPool
from models import Movie, User, UserRating
from auth import get_current_user
import scipy.sparse as sp
from ml.models_code.EASE import EASE


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

##### ml fixtures

@pytest.fixture(name="dummy_matrix")
def dummy_matrix_fixture():
    """
    Creates a small 5-user, 4-item sparse matrix for testing
    """
    # simulated interactions: rows=users, cols=items
    data = [1, 1, 1, 1, 1, 1]
    row_ind = [0, 0, 1, 2, 3, 4]
    col_ind = [0, 1, 1, 2, 3, 3]
    return sp.csr_matrix((data, (row_ind, col_ind)), shape=(5, 4))

@pytest.fixture(name="dummy_data")
def dummy_data_fixture():
    """
    creates a small dataset for testing: [user_id, item_id, rating]
    """
    return np.array([
        [0, 0, 5.0],
        [0, 1, 4.0],
        [1, 0, 3.0],
        [1, 2, 2.0],
        [2, 1, 5.0]
    ], dtype=np.float64)

@pytest.fixture(name="seed_data")
def seed_data_fixture(session):
    """
    Seeds the test database with users, movies, and ratings
    """
    # create movies
    m1 = Movie(id=10, imdb_id="tt01", movie_id="101", title="Movie A", year=2000, type="movie", poster="img.jpg")
    m2 = Movie(id=20, imdb_id="tt02", movie_id="102", title="Movie B", year=2001, type="movie", poster="img.jpg")
    m3 = Movie(id=30, imdb_id="tt03", movie_id="103", title="Movie C", year=2002, type="movie", poster="img.jpg")
    
    # create users
    u1 = User(id=1, email="user1@test.com", hashed_password="pwd", nickname="u1")
    u2 = User(id=2, email="user2@test.com", hashed_password="pwd", nickname="u2")
    
    session.add_all([m1, m2, m3, u1, u2])
    session.commit()
    
    # user 1 rates movies A and B
    r1 = UserRating(user_id=1, movie_id=10, rating=5.0)
    r2 = UserRating(user_id=1, movie_id=20, rating=4.0)
    
    # user 2 rates movie C (to ensure user isolation)
    r3 = UserRating(user_id=2, movie_id=30, rating=3.0)
    
    session.add_all([r1, r2, r3])
    session.commit()

@pytest.fixture
def ease_model_with_mocked_b():
    """
    Returns an unfitted EASE model with a manually injected B matrix
    specifically designed for testing recommendation ordering and negative feedback
    
    Item 0 is mildly similar to 1 and 2
    Item 3 is highly similar to 1, but completely unrelated to 2
    """
    model = EASE()
    model.num_items = 4
    model.B = np.array([
        [0.0, 0.5, 0.4, 0.0],
        [0.5, 0.0, 0.0, 0.9],
        [0.4, 0.0, 0.0, 0.0],
        [0.0, 0.9, 0.0, 0.0]
    ], dtype=np.float32)
    
    return model