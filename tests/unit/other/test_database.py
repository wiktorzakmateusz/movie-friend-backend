from unittest.mock import patch
from sqlmodel import Session
from database import create_db_and_tables, get_session, engine

def test_create_db_and_tables():
    """
    Tests if tables are generated using the correct engine
    """
    # blocks the actual database creation to protect the local sqlite file
    with patch("database.SQLModel.metadata.create_all") as mock_create_all:
        create_db_and_tables()
        
        # verifies the function attempted to use the correct engine
        mock_create_all.assert_called_once_with(engine)

def test_get_session():
    """
    Tests if the generator yields a valid session
    """
    session_gen = get_session()
    session = next(session_gen)
    
    # verifies the yielded object is a sqlmodel session
    assert isinstance(session, Session)
    
    # verifies it is bound to the correct sqlite engine
    assert session.bind == engine
    
    # cleans up the generator
    session.close()
    session_gen.close()