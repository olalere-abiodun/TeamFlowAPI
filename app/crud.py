from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app import schema, model, security


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


# Accept invitation
def accept_invitation(organization_id: int, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if user has a pending invite
    membership = get_membership(db, organization_id, current_user.uid)

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
    membership = get_membership(db, organization_id, current_user.uid)

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
    membership = get_membership(db, organization_id, user_id)

    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of this organization")

    # Remove the member (delete the membership record)
    db.delete(membership)
    db.commit()

# Organization create projects, list projects, get project details, update project, delete project
# create new project

def create_project(organization_id: int, project: schema.ProjectCreate, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner can create projects
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can create projects"
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
    membership = get_membership(db, organization_id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view projects"
        )

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

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view projects"
        )

    project = db.query(model.Project).filter(model.Project.organization_id == organization_id, model.Project.id == project_id).first()
    return project

# update project
def update_project(organization_id: int, project_id: int, project: schema.ProjectCreate, db: Session, current_user: schema.CurrentUser):
    # Check organization exists
    org = db.query(model.Organization).filter(
        model.Organization.id == organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Only owner can update projects
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can update projects"
        )

    db_project = db.query(model.Project).filter(model.Project.organization_id == organization_id, model.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_project.name = project.name
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

    # Authorization: Only owner can delete projects
    if org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization owner can delete projects"
        )

    db_project = db.query(model.Project).filter(model.Project.organization_id == organization_id, model.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(db_project)
    db.commit()

# create board, list boards, get board details, update board, delete board
# create board 
def create_board(project_id: int, board: schema.BoardCreate, db: Session, current_user: schema.CurrentUser):
    # Check project exists and get organization
    project = db.query(model.Project).filter(model.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Authorization: Only organization owner or members can create boards
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()
    membership = get_membership(db, project.organization_id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can create boards"
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

    # Authorization check
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()
    membership = get_membership(db, project.organization_id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
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

    # Authorization check
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()
    membership = get_membership(db, project.organization_id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can view boards"
        )
    board = db.query(model.Board).filter(model.Board.project_id == project_id, model.Board.id == board_id).first()
    return board

#Update board
def update_board(project_id: int, board_id: int, board: schema.BoardCreate, db: Session, current_user: schema.CurrentUser):
    project = db.query(model.Project).filter(model.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Authorization check
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()
    membership = get_membership(db, project.organization_id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can update boards"
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
    membership = get_membership(db, project.organization_id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can delete boards"
        )
    db_board = db.query(model.Board).filter(model.Board.project_id == project_id, model.Board.id == board_id).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board not found")

    db.delete(db_board)
    db.commit()

# create task, list tasks, get task details, update task, delete task
def create_task(board_id: int, task: schema.TaskCreate, db: Session, current_user: schema.CurrentUser):
    # Check board exists and get project and organization
    board = db.query(model.Board).filter(model.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    project = db.query(model.Project).filter(model.Project.id == board.project_id).first()
    org = db.query(model.Organization).filter(model.Organization.id == project.organization_id).first()

    # Authorization: Only organization owner or members can create tasks
    membership = get_membership(db, org.id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="Only organization members can create tasks"
        )

    db_task = model.Task(
        board_id=board_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date
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
        raise HTTPException(404, "Organization not found")

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

    # Base query (IMPORTANT CHANGE)
    query = db.query(model.Task).filter(
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    )

    # Filters
    if status:
        query = query.filter(model.Task.status == status)

    if assignee_id:
        query = query.filter(model.Task.assignee_id == assignee_id)

    if priority:
        query = query.filter(model.Task.priority == priority)

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
        raise HTTPException(404, "Project not found in this organization")

    # Authorization
    membership = get_membership(db, org_id, current_user.uid)

    if not membership:
        raise HTTPException(403, "Not authorized")

    task = db.query(model.Task).filter(
        model.Task.id == task_id,
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    ).first()

    if not task:
        raise HTTPException(404, "Task not found")

    return task

# Update task 
def update_task(org_id: int, project_id: int, task_id: int, task_update: schema.TaskUpdate, db: Session, current_user: schema.CurrentUser):
    # Check organization
    org = db.query(model.Organization).filter(model.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Authorization: Check if user is owner or accepted member
    membership = get_membership(db, org_id, current_user.uid)

    if not membership and org.owner_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to update tasks in this organization")

    # Get the task
    db_task = db.query(model.Task).filter(
        model.Task.id == task_id,
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    ).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields if provided
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

    # Authorization: Only owner can delete tasks
    # Authorization: Check if user is owner or accepted member
    if org.owner_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Only organization owner can delete tasks in this organization")
    # Get the task
    db_task = db.query(model.Task).filter(model.Task.id == task_id,
        model.Task.project_id == project_id,
        model.Task.organization_id == org_id
    ).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    
    

