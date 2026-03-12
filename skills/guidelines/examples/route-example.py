"""
Example: FastAPI route handler with Pydantic validation.

This shows the expected pattern for HTTP route handlers in a Python/FastAPI project.
Validation happens via Pydantic models at the route level. The handler receives
typed, validated input and delegates to a service function.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from enum import Enum

from app.services.pass_service import find_passes_by_teacher
from app.dependencies import get_db


class PassStatus(str, Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class PassResponse(BaseModel):
    id: str
    student_id: str
    teacher_id: str
    status: PassStatus
    created_at: str


router = APIRouter(prefix="/passes", tags=["passes"])


@router.get("/", response_model=list[PassResponse])
async def list_passes(
    teacher_id: str = Query(..., description="Filter by teacher"),
    status: PassStatus | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    return await find_passes_by_teacher(
        db, teacher_id=teacher_id, status=status, limit=limit
    )
