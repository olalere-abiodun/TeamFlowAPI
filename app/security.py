import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from app.schema import CurrentUser
from sqlalchemy.orm import Session
from app.dependencies import get_db
import app.model as model



# JSON is in app/core/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # points to app/
cred_path = os.path.join(BASE_DIR, "core", "teamflowapi-firebase-adminsdk-fbsvc-52cc876a86.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    print(f"Firebase initialized with {cred_path}")

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db)  # ✅ inject DB here
) -> CurrentUser:

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        decoded = auth.verify_id_token(credentials.credentials)

        uid = decoded["uid"]
        email = decoded.get("email")
        email_verified = decoded.get("email_verified", False)

        # 🔒 Block unverified users
        # if not email_verified:
        #     raise HTTPException(
        #         status_code=403,
        #         detail="Please verify your email before accessing this resource"
        #     )

        # 🔍 Get user from DB
        user = db.query(model.User).filter(model.User.uid == uid).first()

        # ➕ Create user if not exists
        if not user:
            user = model.User(
                uid=uid,
                email=email,
                full_name=decoded.get("name") or "Unknown",
                is_verified=email_verified
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 🔄 ✅ UPDATE VERIFICATION STATUS HERE
        if user.is_verified != email_verified:
            user.is_verified = email_verified
            db.commit()

        return CurrentUser(uid=uid, email=email)

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")