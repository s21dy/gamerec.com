import firebase_admin
from firebase_admin import credentials, auth
import sqlite3
import os
import json

#PYTHONPATH=src gunicorn -w 4 -k gevent --threads 2 -b 127.0.0.1:8000 --timeout 120 src.main:app
# Initialize Firebase Admin SDK
service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)
# export FIREBASE_SERVICE_ACCOUNT=$(cat src/firebase-service-account.json)

# Initialize User DB
USER_DB_PATH = os.getenv(
    "USER_DB_PATH", 
    "postgresql://saved_games_user:0Dr4TmfmQCmCfWVUkJUiw7QHxhdgwAz7@dpg-cu7062l6l47c73c4moh0-a.oregon-postgres.render.com/saved_games"
    )

# Initialize the database and tables
def initialize_database():
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL
            )
        ''')
        # Create saved games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                game_id TEXT NOT NULL,
                FOREIGN KEY (uid) REFERENCES users(uid)
            )
        ''')
        conn.commit()


def verify_token(id_token):
    """
    Verify Firebase ID token and return the decoded token.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return None

def get_user_data(uid):
    """
    Retrieve user data from Firebase Authentication.
    """
    try:
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
        }
    except Exception as e:
        return None

def save_user_to_database(uid, email):
    """
    Mock function to save user data to your database.
    Replace with actual database logic.
    """
    try:
        with sqlite3.connect(USER_DB_PATH) as conn:
            cursor = conn.cursor()
            # Insert user into the users table
            cursor.execute('''
                INSERT OR IGNORE INTO users (uid, email)
                VALUES (?, ?)
            ''', (uid, email))
            conn.commit()
        print(f"User {email} saved to the database.")
        return True
    except sqlite3.Error as e:
        print(f"Error saving user to the database: {e}")
        return False
    

