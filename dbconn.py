import os
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
import logging

load_dotenv()

# Database connection settings
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Configure logging
logging.basicConfig(
    filename="user.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    return conn

def ensure_users_table_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL
        ); 
    """)
    conn.commit()
    cursor.close()
    conn.close()

def ensure_farms_table_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farms (
            user_id INT NOT NULL,
            farmname VARCHAR(255) NOT NULL,
            gateway INT NOT NULL,
            PRIMARY KEY (user_id, farmname),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()


# Ensure the user table exists
#ensure_user_table_exists()
