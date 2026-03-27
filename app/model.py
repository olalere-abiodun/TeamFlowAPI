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
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    Organization = relationship("Organization", back_populates="user")
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())
    owner_id = Column(String(128), ForeignKey('users.uid'), nullable=False)

    user = relationship("User", back_populates="organizations")
    invitations = relationship("invitation", back_populates="organization", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")

class invitation(Base):
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
