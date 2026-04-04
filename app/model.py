from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    uid = Column(String(128), primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organizations = relationship("Organization", back_populates="user")
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    file_attachments = relationship("FileAttachment", back_populates="uploader", cascade="all, delete-orphan")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())
    owner_id = Column(String(128), ForeignKey('users.uid'), nullable=False)

    user = relationship("User", back_populates="organizations")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="organization", cascade="all, delete-orphan")

class Invitation(Base):
    __tablename__ = 'invitations'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    organization = relationship("Organization", back_populates="invitations")

class Membership(Base):
    __tablename__ = 'memberships'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    user_id = Column(String(128), ForeignKey('users.uid'), nullable=False)
    role = Column(String(50), default="user")
    status = Column(String(50), default="pending")
    created_at = Column(TIMESTAMP, server_default=func.now())

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", back_populates="projects")
    boards = relationship("Board", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Board(Base):
    __tablename__ = 'boards'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    project = relationship("Project", back_populates="boards")
    tasks = relationship("Task", back_populates="board")

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    board_id = Column(Integer, ForeignKey('boards.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    status = Column(String(50), default="todo")
    priority = Column(String(20), default="medium")
    assignee_id = Column(String, ForeignKey("users.uid"), nullable=True)
    created_by = Column(String, ForeignKey("users.uid"))

    due_date = Column(DateTime, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    board = relationship("Board", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    project = relationship("Project", back_populates="tasks")
    organization = relationship("Organization", back_populates="tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("FileAttachment", back_populates="task", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    author_id = Column(String, ForeignKey('users.uid'), nullable=False)
    comment = Column(String(1000), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")

class FileAttachment(Base):
    __tablename__ = 'file_attachments'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    uploaded_by = Column(String, ForeignKey('users.uid'), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User", back_populates="file_attachments") 