from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from firebase_admin import auth

def sync_verified_users():
    db: Session = SessionLocal()

    try:
        users = db.query(User).filter(User.is_verified == False).all()

        for user in users:
            firebase_user = auth.get_user(user.uid)

            if firebase_user.email_verified:
                user.is_verified = True

        db.commit()
        print("Verification sync completed")

    except Exception as e:
        print("Error in sync:", e)
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_verified_users, 'interval', minutes=5)  # runs every 5 minutes
    scheduler.start()