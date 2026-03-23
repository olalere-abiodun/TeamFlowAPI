import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Annotated

# JSON is in app/core/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # points to app/
cred_path = os.path.join(BASE_DIR, "core", "teamflowapi-firebase-adminsdk-fbsvc-52cc876a86.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    print(f"Firebase initialized with {cred_path}")

bearer_scheme = HTTPBearer(auto_error=False)

class CurrentUser(BaseModel):
    uid: str
    email: str | None = None

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        decoded = auth.verify_id_token(credentials.credentials)
        return CurrentUser(uid=decoded["uid"], email=decoded.get("email"))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")