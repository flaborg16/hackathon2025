from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from datamodels import TokenData
import os
from typing import Optional
import logging
from fastapi import HTTPException, status
from dbconn import get_db_connection
import psycopg2

# Setup logging
logging.basicConfig(
    filename="users.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")  # Default for development
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24*60

def verify_password(plain_password, hashed_password):
    logger.debug("Verifying password")
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    logger.debug("Hashing password")
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    logger.debug("Creating access token")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Access token created: {encoded_jwt}")
    return encoded_jwt

def decode_access_token(token: str):
    logger.debug("Decoding access token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token decode failed: email is None")
            raise JWTError
        logger.info(f"Token decoded successfully: {email}")
        return TokenData(email=email)
    except JWTError as e:
        logger.error(f"Token decode failed: {e}")
        return None

def get_current_user(token: str):
    logger.debug("Getting current user from token")
    token_data = decode_access_token(token)
    if token_data is None:
        logger.warning("Invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (token_data.email,))
        user = cursor.fetchone()
        if user is None:
            logger.warning("User not found")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        logger.info(f"User found: {user['email']}")
        return user
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
        logger.debug("Database connection closed")

# Ensure the user table exists (for context)
#ensure_user_table_exists()
