import firebase_admin
from firebase_admin import credentials, auth
import os

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    # Path to the service account key JSON file
    # The user should download this from the Firebase Console
    cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
    
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # Fallback for environments where the file might not be present
        # e.g., using default credentials or purely env vars if configured
        print(f"Warning: Firebase service account file not found at {cred_path}")
        try:
            firebase_admin.initialize_app()
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")

def verify_firebase_token(id_token):
    """
    Verify a Firebase ID token.
    Returns decoded token if valid, else raises an exception.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise e
