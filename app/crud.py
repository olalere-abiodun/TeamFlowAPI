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

#List all organizations user belongs to
def get_organizations_by_user(organization_id: int, db: Session, current_user: schema.CurrentUser):
    db_organization = db.query(model.Organization).filter(model.Organization.owner_id == current_user.uid).all()
    return db_organization
    
#Get organization details
def get_organization(organization_id: int, db: Session, current_user: schema.CurrentUser):
    db_organization = db.query(model.Organization).filter(model.Organization.id == organization_id).first()
    return db_organization

# Update organization
def update_organization(organization_id: int, db: Session, current_user: schema.CurrentUser, organization: schema.UpdateOrganization):
    db_organization = model.Organization(
        name = organization.name,
        description = organization.description
        )
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization

#Delete organization
def delete_organization(organization_id: int, db: Session, current_user: schema.CurrentUser):
    db_organization = db.query(model.Organization).filter(model.Organization.id == organization_id).first()
    if db_organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    db.delete(db_organization)
    db.commit()


