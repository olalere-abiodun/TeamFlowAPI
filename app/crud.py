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

#List all organizations user Owned
def get_my_organizations(db: Session, current_user: schema.CurrentUser):
    db_organization = db.query(model.Organization).filter(model.Organization.owner_id == current_user.uid).all()
    return db_organization

#List all organizations user is a member of
def get_member_organizations(db: Session, current_user: schema.CurrentUser):
    db_organizations = db.query(model.Organization).join(model.Membership, model.Organization.id == model.Membership.organization_id).filter(model.Membership.user_id == current_user.uid).all()
    return db_organizations   

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

#store invitation
def invite_member( invitation: schema.InvitationCreate, db: Session):
    db_invitation = model.invitation(
        organization_id=invitation.organization_id,
        email=invitation.email
    )
    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)
    return db_invitation

#List pending invites
def list_pending_invites(organization_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner can view
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can view pending invites"
        )

    # Get only pending invites
    pending_invites = db.query(model.Membership).filter(model.Membership.organization_id == organization_id, model.Membership.status == "pending").all()
    return pending_invites

# List all members of an organization
def list_members(organization_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner can view
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can view members"
        )

    members = db.query(model.Membership).filter(model.Membership.organization_id == organization_id).all()
    return members

# Accept invitation
def accept_invitation(organization_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if user has a pending invite
    membership = db.query(model.Membership).filter(
        model.Membership.organization_id == organization_id,
        model.Membership.user_id == current_user.uid,
        model.Membership.status == "pending"
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="No pending invitation found for this user")

    # Accept the invitation
    membership.status = "accepted"
    db.commit()
    db.refresh(membership)
    return membership

# Reject invitation
def reject_invitation(organization_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if user has a pending invite
    membership = db.query(model.Membership).filter(
        model.Membership.organization_id == organization_id,
        model.Membership.user_id == current_user.uid,
        model.Membership.status == "pending"
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="No pending invitation found for this user")

    # Reject the invitation (delete the membership record)
    db.delete(membership)
    db.commit()

# Remove member from organization
def remove_member(organization_id: int, user_id: str, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner can remove members
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can remove members"
        )

    # Check if user is a member
    membership = db.query(model.Membership).filter(
        model.Membership.organization_id == organization_id,
        model.Membership.user_id == user_id,
        model.Membership.status == "accepted"
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of this organization")

    # Remove the member (delete the membership record)
    db.delete(membership)
    db.commit()
