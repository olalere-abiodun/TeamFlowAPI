from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app import schema, model, security
from app.dependencies import get_db


def create_organization( organization: schema.createOrganization, db: Session, current_user: schema.CurrentUser):
    db_organization = model.Organization(
        name=organization.name,
        description=organization.description,
        owner_id=current_user.uid
    )
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization

# def get_organization_by_id(organization_id: int, db: Session = Depends(get_db),current_user: schema.CurrentUser = Depends(security.get_current_user)):
#     db_organization = db.query(model.Organization).filter(model.Organization.id == organization_id ).first()
#     if db_organization is None:
#         raise HTTPException(status_code=404, detail="Organization not found")

# def get_organizations(db: Session = Depends(get_db)):
#     return db.query(model.Organization).all()

# def update_organization(organization_id: int, organization: schema.UpdateOrganization, db: Session = Depends(get_db)):
#     db_organization = get_organization_by_id(organization_id, db)
#     for key, value in organization.dict(exclude_unset=True).items():
#         setattr(db_organization, key, value)
