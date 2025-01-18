import firebase_admin
from firebase_admin import credentials, auth
from flask import request, jsonify

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

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
    print(f"Saving user: {uid}, email: {email}")
    # Implement database save logic here
    return True
