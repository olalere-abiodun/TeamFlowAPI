# pylint: disable=invalid-name
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app import schema, model, security
from app.dependencies import get_db
from app.security import get_current_user
from app.model import User
import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials, initialize_app
from app.routers.util import send_email
from fastapi import BackgroundTasks

load_dotenv()

cred_env = os.getenv("FIREBASE_CRED_PATH")

if not cred_env:
    raise Exception("FIREBASE_CRED_PATH not set in .env")

cred_path = os.path.abspath(cred_env)

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)


router = APIRouter(prefix="/auth", tags=["User Authentication Operations"])


@router.post("/register")
def register_user(user: schema.UserCreate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        # Create user in Firebase Authentication
        firebase_user = auth.create_user(
            email=user.email,
            display_name=user.full_name,
            password=user.password
        )

        # Create user in local database
        new_user = User(
            uid=firebase_user.uid,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        link = auth.generate_email_verification_link(firebase_user.email)

        # Send email (non-blocking logic)
        try:
            background_tasks.add_task(send_email, user.email, link)
        except Exception as email_error:
            print("Email sending failed:", email_error)

        return {
            "message": "User registered successfully. Verification email sent.",
            "user": {
                "uid": new_user.uid,
                "name": new_user.full_name,
                "email": new_user.email
            }
        }

    except Exception as e:
        db.rollback()

        try:
            if 'firebase_user' in locals():
                auth.delete_user(firebase_user.uid)
        except:
            pass

        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login_user():
    # Login is handled on the client side using Firebase Authentication SDKs.
    # This endpoint can be used to provide any additional server-side logic if needed.
    return {"message": "Login should be handled on the client side using Firebase Authentication SDKs."}

@router.get("/me")
def get_me(current_user: schema.CurrentUser = Depends(get_current_user),db: Session = Depends(get_db)):
    user = db.query(User).filter(User.uid == current_user.uid).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")

    try:
        # Get latest Firebase user state
        firebase_user = auth.get_user(current_user.uid)

        # Sync email verification status
        if user.is_verified != firebase_user.email_verified:
            user.is_verified = firebase_user.email_verified
            db.commit()
            db.refresh(user)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase sync failed: {str(e)}")

    return user



@router.post("/send-verification-email")
def send_verification_email(
    current_user: schema.CurrentUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    try:
        firebase_user = auth.get_user(current_user.uid)

        # Prevent spam if already verified
        if firebase_user.email_verified:
            raise HTTPException(status_code=400, detail="Email already verified")

        # Generate link
        link = auth.generate_email_verification_link(current_user.email)

        # Send email
        if background_tasks:
            background_tasks.add_task(send_email, current_user.email, link)
        else:
            send_email(current_user.email, link)

        return {"message": "Verification email sent successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Refresh access token endpoint (if needed for server-side sessions)
@router.post("/refresh-token")
def refresh_token():
    # Token refresh is typically handled on the client side using Firebase Authentication SDKs.
    return {"message": "Token refresh should be handled on the client side using Firebase Authentication SDKs."}

# logout 
@router.post("/logout")
def logout_user():
    # Logout is handled on the client side by clearing the user's authentication state.
    return {"message": "Logout should be handled on the client side by clearing the user's authentication state."}

# google oauth login 
@router.post("/google-login")
def google_login():
    # Google OAuth login is handled on the client side using Firebase Authentication SDKs.
    return {"message": "Google OAuth login should be handled on the client side using Firebase Authentication SDKs."}
