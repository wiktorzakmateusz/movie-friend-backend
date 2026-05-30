from security import get_password_hash, verify_password

def test_get_password_hash():
    """
    Tests if password is encrypted and differs from plaintext
    """
    plain_password = "my_super_secret_password"
    hashed_password = get_password_hash(plain_password)
    
    assert hashed_password != plain_password
    assert hashed_password.startswith("$2") 
    assert len(hashed_password) > 20

def test_verify_password_success():
    """
    Tests successful password verification
    """
    plain_password = "secure_password"
    hashed_password = get_password_hash(plain_password)
    
    result = verify_password(plain_password, hashed_password)
    
    assert result is True

def test_verify_password_failure():
    """
    Tests failing verification with wrong password
    """
    plain_password = "secure_password"
    wrong_password = "wrong_password"
    hashed_password = get_password_hash(plain_password)
    
    result = verify_password(wrong_password, hashed_password)
    
    assert result is False