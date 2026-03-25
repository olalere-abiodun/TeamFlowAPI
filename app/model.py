from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    uid = Column(String(128), primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)

    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
