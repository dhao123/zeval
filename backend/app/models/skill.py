"""
Skill/Rule model.
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.standard import Standard
    from app.models.synthetic import SyntheticData
    from app.models.user import User


class Skill(Base):
    """Skill/Rule model extracted from standards."""
    
    __tablename__ = "skills"
    
    skill_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category_l4: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    rules: Mapped[dict] = mapped_column(JSON, nullable=False)
    prompt_template: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    
    # Foreign keys
    standard_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("standards.standard_id"), index=True
    )
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    standard: Mapped[Optional["Standard"]] = relationship("Standard", back_populates="skills")
    creator: Mapped[Optional["User"]] = relationship("User")
    synthetics: Mapped[List["SyntheticData"]] = relationship(
        "SyntheticData", back_populates="skill"
    )
