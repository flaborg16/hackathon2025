from fastapi import FastAPI, HTTPException, Depends, status, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from dbconn import *
from helperfunctions import *
from datamodels import *
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import json  # Import json for JSON operations
from typing import Optional, List
from datetime import timedelta

app = FastAPI()

# Setup logging
logging.basicConfig(
    filename="users.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure tables exist
ensure_users_table_exists()
ensure_farms_table_exists()

# Set all CORS enabled origins
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:3001"
    # Add other origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@app.post("/register", response_model=UserRegistration)
async def register_user(user: UserCreate):
    logger.info(f"Received registration request: {user.json()}")
    ensure_users_table_exists()
    ensure_farms_table_exists()
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
        db_user = cursor.fetchone()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = get_password_hash(user.password)
        cursor.execute(
            "INSERT INTO users (email, password, name) VALUES (%s, %s, %s) RETURNING user_id, email, name",
            (user.email, hashed_password, user.name)
        )
        new_user = cursor.fetchone()
        conn.commit()
        return new_user
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        cursor.close()
        conn.close()


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (form_data.username,))
        user = cursor.fetchone()
        if not user or not verify_password(form_data.password, user['password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user['email']}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        cursor.close()
        conn.close()


@app.get("/users/me", response_model=UserRegistration)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    logger.info("Fetching current user")
    current_user = get_current_user(token)
    return current_user


# ----- Farm Endpoints (No OAuth/token verification) -----

@app.options("/{rest_of_path:path}")
async def options_handler():
    return

@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    body = await request.body()
    logger.error(f"Validation error for request body: {body}")
    logger.error(f"Validation error details: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {request.headers}")
    logger.info(f"Request body: {await request.body()}")
    response = await call_next(request)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
