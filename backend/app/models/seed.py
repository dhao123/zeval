"""
Seed data model.
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.synthetic import SyntheticData
    from app.models.user import User


class Seed(Base):
    """Seed data model."""
    
    __tablename__ = "seeds"
    
    seed_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    gt: Mapped[dict] = mapped_column(JSON, nullable=False)
    category_l4: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category_path: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    
    # Foreign keys
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    confirmed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by], back_populates="created_seeds"
    )
    confirmer: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[confirmed_by], back_populates="confirmed_seeds"
    )
    synthetics: Mapped[List["SyntheticData"]] = relationship(
        "SyntheticData", back_populates="seed"
    )
