from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schema, model, security
from app.dependencies import get_db
from app.security import get_current_user
from app.model import User
from firebase_admin import auth



router = APIRouter(prefix="/auth", tags=["User Authentication Operations"])

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