from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schema, model, crud
from app.dependencies import get_db
from app.security import get_current_user



router = APIRouter(prefix="/Organization", tags=["Organization Operations"])

@router.post("/", response_model=schema.OrganizationResponce)
def create_organization(organization: schema.createOrganization , db: Session = Depends(get_db), current_user: schema.CurrentUser = Depends(get_current_user)):
    db_organization = crud.create_organization(organization = organization, db=db, current_user=current_user.uid)
    return db_organization




    

