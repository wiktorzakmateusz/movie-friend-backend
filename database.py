from sqlmodel import SQLModel, Session, create_engine
import os

# sqlite location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")

# SQLite connection URL
sqlite_url = f"sqlite:///{db_path}"

# SQLAlchemy engine that manages database connections
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """
    Creates database and tables if they don't exist
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Generator function used as a FastAPI Dependency whenever 
    an endpoint needs to talk to the database
    """
    with Session(engine) as session:
        yield session