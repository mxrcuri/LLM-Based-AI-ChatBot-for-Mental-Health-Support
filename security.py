from passlib.context import CryptContext

# Create a CryptContext with the bcrypt algorithm.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.
    
    :param password: The plain-text password to hash.
    :return: A hashed version of the password.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.
    
    :param plain_password: The plain-text password entered by the user.
    :param hashed_password: The hashed password stored in the database.
    :return: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
