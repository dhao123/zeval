"""
User and Role models.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.types import JSON
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.synthetic import SyntheticData


class Role(Base):
    """Role model for RBAC."""
    
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256))
    permissions: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))
    department: Mapped[Optional[str]] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users")
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation", back_populates="submitter"
    )
    confirmed_synthetics: Mapped[List["SyntheticData"]] = relationship(
        "SyntheticData",
        foreign_keys="SyntheticData.confirmed_by",
        back_populates="confirmer",
    )
    created_seeds: Mapped[List["Seed"]] = relationship(
        "Seed",
        foreign_keys="Seed.created_by",
        back_populates="creator",
    )
    confirmed_seeds: Mapped[List["Seed"]] = relationship(
        "Seed",
        foreign_keys="Seed.confirmed_by",
        back_populates="confirmer",
    )
