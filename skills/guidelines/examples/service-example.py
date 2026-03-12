"""
Example: Service function with explicit dependencies and result types.

Plain functions, not class methods. The database session is passed in as a
parameter. Errors are returned as result types, not raised as exceptions
(exceptions are reserved for truly unexpected failures).
"""

from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pass_model import Pass, PassStatus


class PassError(str, Enum):
    not_found = "not_found"
    already_completed = "already_completed"
    unauthorized = "unauthorized"


@dataclass
class Ok[T]:
    value: T


@dataclass
class Err:
    error: PassError
    message: str


type Result[T] = Ok[T] | Err


async def find_passes_by_teacher(
    db: AsyncSession,
    *,
    teacher_id: str,
    status: PassStatus | None = None,
    limit: int = 50,
) -> list[Pass]:
    query = select(Pass).where(Pass.teacher_id == teacher_id)
    if status is not None:
        query = query.where(Pass.status == status)
    query = query.limit(limit).order_by(Pass.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def complete_pass(db: AsyncSession, *, pass_id: str) -> Result[Pass]:
    result = await db.execute(select(Pass).where(Pass.id == pass_id))
    hall_pass = result.scalar_one_or_none()

    if hall_pass is None:
        return Err(PassError.not_found, f"Pass {pass_id} not found")

    if hall_pass.status == PassStatus.completed:
        return Err(PassError.already_completed, f"Pass {pass_id} already completed")

    hall_pass.status = PassStatus.completed
    await db.commit()
    await db.refresh(hall_pass)
    return Ok(hall_pass)
