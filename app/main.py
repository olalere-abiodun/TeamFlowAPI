from fastapi import FastAPI, Depends
from app.security import get_current_user, CurrentUser

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TeamFlowAPI running 🚀"}

@app.get("/test-auth")
def test_auth(user: CurrentUser = Depends(get_current_user)):
    return {
        "message": "Authentication successful ✅",
        "user": user
    }