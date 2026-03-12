"""
Example: SQLAlchemy model + Pydantic schema separation.

SQLAlchemy handles persistence. Pydantic handles validation at boundaries.
Keep them separate: models define what's stored, schemas define what's accepted
and returned.
"""

import enum
from datetime import datetime

from sqlalchemy import String, Enum as SAEnum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pydantic import BaseModel, Field


# --- SQLAlchemy models (persistence) ---


class Base(DeclarativeBase):
    pass


class PassStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class Pass(Base):
    __tablename__ = "passes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("students.id"), nullable=False
    )
    teacher_id: Mapped[str] = mapped_column(
        String, ForeignKey("teachers.id"), nullable=False
    )
    status: Mapped[PassStatus] = mapped_column(
        SAEnum(PassStatus), default=PassStatus.active, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Pydantic schemas (boundaries) ---


class CreatePassInput(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    teacher_id: str = Field(..., description="UUID of the requesting teacher")
    notes: str | None = Field(None, max_length=500)


class PassResponse(BaseModel):
    id: str
    student_id: str
    teacher_id: str
    status: PassStatus
    created_at: datetime

    model_config = {"from_attributes": True}
