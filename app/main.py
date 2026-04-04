from fastapi import FastAPI, Depends
from app.security import get_current_user, CurrentUser
from app.database import Base, engine
from app.routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)



@app.get("/")
def home():
    return {"message": "TeamFlowAPI running"}
