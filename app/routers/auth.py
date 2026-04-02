from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schema, model, security
from app.dependencies import get_db
from app.security import get_current_user
from app.model import User
from firebase_admin import auth

router = APIRouter(prefix="/auth", tags=["User Authentication Operations"])


@router.post("/register")
def register_user(user: schema.UserCreate, db: Session = Depends(get_db)):
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

        return {"message": "User registered successfully", 
                "user": {
                    "uid": new_user.uid,
                    "name": new_user.full_name,
                    "email": new_user.email}
                    }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login_user():
    # Login is handled on the client side using Firebase Authentication SDKs.
    # This endpoint can be used to provide any additional server-side logic if needed.
    return {"message": "Login should be handled on the client side using Firebase Authentication SDKs."}

@router.get("/me", response_model=schema.CurrentUser)
def get_me(current_user: schema.CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.uid == current_user.uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")

    return schema.CurrentUser(uid=user.uid, email=user.email)


@router.post("/send-verification-email")
def send_verification_email(current_user: schema.CurrentUser = Depends(get_current_user)):
    try:
        # 🔗 Generate verification link
        link = auth.generate_email_verification_link(current_user.email)

        return {
            "message": "Verification email link generated",
            "verification_link": link  # ⚠️ For testing only
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

# google oauth login2 
@router.post("/google-login2")
def google_login2():
    # Google OAuth login is handled on the client side using Firebase Authentication SDKs.
    return {"message": "Google OAuth login should be handled on the client side using Firebase Authentication SDKs."}