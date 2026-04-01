from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app import schema, model, security
import shutil
import os
import uuid


# Helper function 
def get_membership(db: Session, org_id: int, user_id: str):
    membership = db.query(model.Membership).filter(
        model.Membership.organization_id == org_id,
        model.Membership.user_id == user_id,
        model.Membership.status == "accepted"
    ).first()

    if not membership:
        raise HTTPException(403, "Not authorized")

    return membership

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
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner or members can view
    membership = get_membership(db, organization_id,current_user.uid )

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this organization"
        )
    return org

# Update organization
def update_organization(organization_id: int, db: Session, current_user: schema.CurrentUser, organization: schema.UpdateOrganization):
    db_organization = db.query(model.Organization).filter(model.Organization.id == organization_id).first()
    if db_organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    # Authorization: Only owner can update
    if db_organization.owner_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Only organization owner can update the organization")
    # Update fields
    if organization.name is not None:
        db_organization.name = organization.name
    if organization.description is not None:
        db_organization.description = organization.description

    db.commit()
    db.refresh(db_organization)
    return db_organization
    
 #Delete organization
def delete_organization(organization_id: int, db: Session, current_user: schema.CurrentUser):
    db_organization = db.query(model.Organization).filter(model.Organization.id == organization_id).first()
    if db_organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    # Authorization: Only owner can delete
    if db_organization.owner_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Only organization owner can delete the organization")
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

    # Reject the invitation
    membership.status = "rejected"

    db.commit()
    db.refresh(membership)

    return {"message": "Invitation rejected"}

# Organization owner add admin
def add_admin(organization_id: int, user_id: str, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner can add admin
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can add admins"
        )

    # Check if user is a member
    membership = get_membership(db, organization_id, user_id)

    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of this organization")

    # Update role to admin
    membership.role = "admin"
    db.commit()
    db.refresh(membership)
    return membership

# Remove member from organization
def remove_member(organization_id: int, user_id: str, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner and admin can remove members
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can remove members"
        )

    # Check if user is a member
    current_membership = get_membership(db, organization_id, current_user.uid)
    # Authorization: owner or admin
    if current_membership.role not in ["owner", "admin"]:
        raise HTTPException(403, "Not authorized to remove members")

    # Get target user membership
    target_membership = db.query(model.Membership).filter(
        model.Membership.organization_id == organization_id,
        model.Membership.user_id == user_id
    ).first()

    if not target_membership:
        raise HTTPException(404, "User is not a member of this organization")

    # Prevent removing owner
    if target_membership.role == "owner":
        raise HTTPException(403, "Cannot remove organization owner")

    #  Admin cannot remove another admin (optional rule)
    if (
        current_membership.role == "admin" and
        target_membership.role == "admin"
    ):
        raise HTTPException(403, "Admin cannot remove another admin")

    #  Prevent self-removal (optional)
    if user_id == current_user.uid:
        raise HTTPException(400, "You cannot remove yourself")

    # Remove member
    db.delete(target_membership)
    db.commit()

    return {"message": "Member removed successfully"}


# Organization create projects, list projects, get project details, update project, delete project
# create new project

def create_project(organization_id: int, project: schema.ProjectCreate, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner and admin can create projects
    membership = get_membership(db, organization_id, current_user.uid)

    if membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner and admin can create projects"
        )
    db_project = model.Project(
        organization_id=organization_id,
        name=project.name,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

# List projects in an organization with pagination and filter 
def list_projects(organization_id: int, db: Session, current_user: schema.CurrentUser, skip: int = 0, limit: int = 10):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only members can view projects
    get_membership(db, organization_id, current_user.uid)

    projects = db.query(model.Project).filter(model.Project.organization_id == organization_id).offset(skip).limit(limit).all()
    return projects

# Get single project details 
def get_project(organization_id: int, project_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only members can view projects
    membership = get_membership(db, organization_id, current_user.uid)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view projects"
        )

    project = db.query(model.Project).filter(model.Project.organization_id == organization_id, model.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# update project
def update_project(
    organization_id: int,
    project_id: int,
    project: schema.ProjectUpdate,
    db: Session,
    current_user: schema.CurrentUser
):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization (RBAC)
    membership = get_membership(db, organization_id, current_user.uid)

    if membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only owner or admin can update projects"
        )

    # Get project
    db_project = db.query(model.Project).filter(
        model.Project.organization_id == organization_id,
        model.Project.id == project_id
    ).first()

    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Partial update
    if project.name is not None:
        db_project.name = project.name

    if project.description is not None:
        db_project.description = project.description

    db.commit()
    db.refresh(db_project)

    return db_project

# Delete project

def delete_project(organization_id: int, project_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner and admin can delete projects
    membership = get_membership(db, organization_id, current_user.uid)

    if membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only owner or admin can delete projects"
        )

    # Get project
    db_project = db.query(model.Project).filter(
        model.Project.organization_id == organization_id,
        model.Project.id == project_id
    ).first()

    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete project
    db.delete(db_project)
    db.commit()

    return {"message": "Project deleted successfully"}

# create board, list boards, get board details, update board, delete board
# create board 
def create_board(project_id: int, board: schema.BoardCreate, db: Session, current_user: schema.CurrentUser):
    # Check project exists and get organization
    project = db.query(model.Project).filter(model.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Authorization: Only organization owner or members can create boards
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    membership = get_membership(db, project.organization_id, current_user.uid)
    if membership.role not in ["owner", "admin"]:
         raise HTTPException(
            status_code=403,
            detail="Only organization owner and admin can create boards"
        )

    db_board = model.Board(
        project_id=project_id,
        name=board.name,
        description=board.description
    )
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    return db_board

# List boards in a project
def list_boards(project_id: int, db: Session, current_user: schema.CurrentUser):
    project = db.query(model.Project).filter(model.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == project.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization check
    membership = get_membership(db, project.organization_id, current_user.uid)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view boards"
        )
    boards = db.query(model.Board).filter(model.Board.project_id == project_id).all()
    return boards

# get board details 
def get_board(project_id: int, board_id: int, db: Session, current_user: schema.CurrentUser):
    project = db.query(model.Project).filter(model.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    membership = get_membership(db, project.organization_id, current_user.uid)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view boards"
        )
    board = db.query(model.Board).filter(model.Board.project_id == project_id, model.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board

#Update board
def update_board(project_id: int, board_id: int, board: schema.BoardCreate, db: Session, current_user: schema.CurrentUser):
    project = db.query(model.Project).filter(model.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Authorization check
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    membership = get_membership(db, project.organization_id, current_user.uid)

    if membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only organization owners and admins can update boards"
        )
    db_board = db.query(model.Board).filter(model.Board.project_id == project_id, model.Board.id == board_id).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board not found")

    db_board.name = board.name
    db_board.description = board.description
    db.commit()
    db.refresh(db_board)
    return db_board

# delete board
def delete_board(project_id: int, board_id: int, db: Session, current_user: schema.CurrentUser):
    project = db.query(model.Project).filter(model.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Authorization check
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    membership = get_membership(db, project.organization_id, current_user.uid)

    if membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only organization owners and admins can delete boards"
        )
    db_board = db.query(model.Board).filter(model.Board.project_id == project_id, model.Board.id == board_id).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board not found")

    db.delete(db_board)
    db.commit()

# create task, list tasks, get task details, update task, delete task
def create_task(board_id: int, task: schema.TaskCreate, db: Session, current_user: schema.CurrentUser):
    #  Check board exists
    board = db.query(model.Board).filter(
        model.Board.id == board_id
    ).first()

    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    #  Get project
    project = db.query(model.Project).filter(
        model.Project.id == board.project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    #  Check creator membership + role
    membership = get_membership(
        db,
        project.organization_id,
        current_user.uid
    )

    if membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and admins can create tasks"
        )

    #  Validate assignee (if provided)
    assignee_id = task.assignee_id if hasattr(task, "assignee_id") else None

    if assignee_id:
        assignee = db.query(model.User).filter(
            model.User.uid == assignee_id
        ).first()

        if not assignee:
            raise HTTPException(
                status_code=404,
                detail="Assignee not found"
            )

        # Ensure assignee belongs to same organization
        assignee_membership = get_membership(
            db,
            project.organization_id,
            assignee_id
        )

        if not assignee_membership:
            raise HTTPException(
                status_code=400,
                detail="Assignee is not a member of this organization"
            )

    # Create task
    db_task = model.Task(
        board_id=board_id,
        project_id=project.id,
        organization_id=project.organization_id,
        title=task.title,
        description=task.description,
        status=task.status.value if hasattr(task.status, "value") else task.status,
        priority=task.priority.value if hasattr(task.priority, "value") else task.priority,
        due_date=task.due_date,
        created_by=current_user.uid, 
        assignee_id=assignee_id        
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task

# list task 
def list_tasks(org_id: int, project_id: int, db: Session, current_user: schema.CurrentUser, status: str = None, assignee_id: str = None, priority: str = None, skip: int = 0, limit: int = 20):
    # Check organization
    org = db.query(model.Organization).filter(
        model.Organization.id == org_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail= "Organization not found")

    # Check project belongs to org
    project = db.query(model.Project).filter(
        model.Project.id == project_id,
        model.Project.organization_id == org_id
    ).first()

    if not project:
        raise HTTPException(404, "Project not found in this organization")

    # Authorization
    membership = get_membership(db, org_id, current_user.uid)

    if not membership:
        raise HTTPException(403, "Not authorized")

    # Base query
    query = db.query(model.Task).filter(
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    )

    # Filters
    if status:
        query = query.filter(model.Task.status == status.value if hasattr(status, "value") else status)

    if assignee_id:
        query = query.filter(model.Task.assignee_id == assignee_id)

    if priority:
        query = query.filter(model.Task.priority == priority.value if hasattr(priority, "value") else priority)

    # Pagination
    tasks = query.offset(skip).limit(limit).all()

    return tasks

# Get Single Task details
def get_task(org_id: int, project_id: int, task_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization
    org = db.query(model.Organization).filter(
        model.Organization.id == org_id
    ).first()

    if not org:
        raise HTTPException(404, "Organization not found")

    # Check project belongs to org
    project = db.query(model.Project).filter(
        model.Project.id == project_id,
        model.Project.organization_id == org_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")

    # Authorization
    membership = get_membership(db, org_id, current_user.uid)

    if not membership:
        raise HTTPException(status_code=403, detail="Not authorized")

    task = db.query(model.Task).filter(
        model.Task.id == task_id,
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

# Update task 
def update_task(
    org_id: int,
    project_id: int,
    task_id: int,
    task_update: schema.TaskUpdate,
    db: Session,
    current_user: schema.CurrentUser
):
    # 🔍 Check organization
    org = db.query(model.Organization).filter(
        model.Organization.id == org_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 🔍 Check project belongs to org
    project = db.query(model.Project).filter(
        model.Project.id == project_id,
        model.Project.organization_id == org_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")

    # 🔍 Get task
    db_task = db.query(model.Task).filter(
        model.Task.id == task_id,
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    ).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 🔒 ONLY CREATOR CAN UPDATE
    if db_task.created_by != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only the task creator can update this task"
        )

    update_data = task_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)

    return db_task


# Delete task
def delete_task(org_id: int, project_id: int, task_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization
    org = db.query(model.Organization).filter(model.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get the task
    db_task = db.query(model.Task).filter(model.Task.id == task_id,
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    ).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if db_task.created_by != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only the task creator can delete this task"
        )


    db.delete(db_task)
    db.commit()
    
#assign and unassign user to task
def assign_task(org_id: int, project_id: int, task_id: int, assignee_id: str, db: Session, current_user: schema.CurrentUser):
    # Check organization
    org = db.query(model.Organization).filter(model.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get the task
    db_task = db.query(model.Task).filter(model.Task.id == task_id,
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    ).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Only creator can assign/unassign
    if db_task.created_by != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only the task creator can assign or unassign this task"
        )
    if assignee_id:
        # Validate assignee
        assignee = db.query(model.User).filter(model.User.uid == assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")

        # Ensure assignee belongs to same organization
        assignee_membership = get_membership(db, org_id, assignee_id)
        if not assignee_membership:
            raise HTTPException(status_code=400, detail="Assignee is not a member of this organization") 
          
    db_task.assignee_id = assignee_id
    db.commit()
    db.refresh(db_task)
    return db_task  

# Add Comment to task 
def add_comment(task_id: int, content: schema.CommentCreate, db: Session, current_user: schema.CurrentUser):
    # Check task exists
    task = db.query(model.Task).filter(model.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == task.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization check
    membership = get_membership(db, task.organization_id, current_user.uid)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can comment on tasks"
        )

    db_comment = model.Comment(
        task_id=task_id,
        author_id=current_user.uid,
        comment=content.comment
    )

    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    return db_comment

# list comments 
def list_comments(task_id: int, db: Session, current_user: schema.CurrentUser):
    # Check task exists
    task = db.query(model.Task).filter(model.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == task.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization check
    membership = get_membership(db, task.organization_id, current_user.uid)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view comments on tasks"
        )

    comments = db.query(model.Comment).filter(model.Comment.task_id == task_id).all()
    return comments

# Edit comment 
def edit_comment(comment_id: int, content: schema.CommentCreate, db: Session, current_user: schema.CurrentUser):
    db_comment = db.query(model.Comment).filter(model.Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if db_comment.author_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only the comment author can edit this comment"
        )

    db_comment.comment = content.comment
    db.commit()
    db.refresh(db_comment)
    return db_comment

# Delete comment
def delete_comment(comment_id: int, db: Session, current_user: schema.CurrentUser):
    db_comment = db.query(model.Comment).filter(model.Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if db_comment.author_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only the comment author can delete this comment"
        )

    db.delete(db_comment)
    db.commit()

# file attachment 
# Upload file to task 
import os
import shutil
import uuid
from fastapi import HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session

def upload_file(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schema.CurrentUser = Depends(get_current_user)
):
    # Check task exists
    task = db.query(model.Task).filter(model.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == task.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization check
    membership = get_membership(db, task.organization_id, current_user.uid)
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can upload files to tasks"
        )

    # Ensure folder exists
    task_folder = f"files/tasks/{task_id}"
    os.makedirs(task_folder, exist_ok=True)

    filename = os.path.basename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"

    file_location = f"{task_folder}/{unique_name}"

    # Save file
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save record in DB
    db_attachment = model.FileAttachment(
        task_id=task_id,
        filename=filename,
        filepath=file_location,
        uploaded_by=current_user.uid
    )

    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return db_attachment

# list all task attachments 
def list_attachments(task_id: int, db: Session, current_user: schema.CurrentUser):
    # Check task exists
    task = db.query(model.Task).filter(model.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == task.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization check
    membership = get_membership(db, task.organization_id, current_user.uid)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view attachments on tasks"
        )

    attachments = db.query(model.FileAttachment).filter(model.FileAttachment.task_id == task_id).all()
    return attachments

# delete file attachment
import os
from fastapi import HTTPException

def delete_attachment(attachment_id: int, db: Session, current_user: schema.CurrentUser):
    attachment = db.query(model.FileAttachment).filter(
        model.FileAttachment.id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # ✅ Check if user is the uploader (owner of the file)
    if attachment.uploaded_by != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="You can only delete files you uploaded"
        )

    # ✅ Delete file from storage
    if attachment.filepath and os.path.exists(attachment.filepath):
        os.remove(attachment.filepath)

    # ✅ Delete record from DB
    db.delete(attachment)
    db.commit()

    return {"detail": "Attachment deleted successfully"}