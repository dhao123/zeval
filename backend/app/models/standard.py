"""
Standard document model.
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.synthetic import SyntheticData
    from app.models.user import User


class Standard(Base):
    """GB/T standard document model."""
    
    __tablename__ = "standards"
    
    standard_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(32))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    parsed_content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    
    # Foreign keys
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    creator: Mapped[Optional["User"]] = relationship("User")
    skills: Mapped[List["Skill"]] = relationship("Skill", back_populates="standard")
    synthetics: Mapped[List["SyntheticData"]] = relationship(
        "SyntheticData", back_populates="standard"
    )
