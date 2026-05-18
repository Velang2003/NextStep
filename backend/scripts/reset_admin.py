import firebase_admin
from firebase_admin import auth, credentials
import os
from app import create_app, db
from app.models.user import User

def reset_admin_account():
    # 1. Initialize Firebase Admin
    service_account_path = 'firebase-service-account.json'
    if not os.path.exists(service_account_path):
        print(f"Error: {service_account_path} not found.")
        return

    cred = credentials.Certificate(service_account_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    email = "whitedevilvelan@gmail.com"
    new_password = "AdminPassword123!"

    print(f"Attempting to reset account: {email}")

    try:
        # 2. Update/Create in Firebase
        try:
            fb_user = auth.get_user_by_email(email)
            auth.update_user(fb_user.uid, password=new_password)
            print(f"Successfully updated Firebase password for UID: {fb_user.uid}")
        except auth.UserNotFoundError:
            fb_user = auth.create_user(email=email, password=new_password)
            print(f"Created NEW Firebase user with UID: {fb_user.uid}")

        # 3. Update/Create in Local Database
        app = create_app()
        with app.app_context():
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(email=email, google_id=fb_user.uid, is_admin=True, is_verified=True)
                db.session.add(user)
                print("Created user in local database.")
            else:
                user.is_admin = True
                user.google_id = fb_user.uid
                print("Updated existing user to Admin in local database.")
            
            db.session.commit()
            print("\n" + "="*40)
            print(f"SUCCESS!")
            print(f"Email: {email}")
            print(f"New Password: {new_password}")
            print("="*40)
            print("You can now use these credentials to Sign In.")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    reset_admin_account()
