"""Smena (shift) API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_operator
from app.database import get_db
from app.models.operator import Operator
from app.models.shift import Change
from app.services.shift_service import (
    ShiftError, close_shift, get_active_shift, get_shift_summary, open_shift,
)
from app.hardware.mariya.driver import get_trk_driver

router = APIRouter(prefix="/shifts", tags=["shifts"])


class OpenShiftRequest(BaseModel):
    pass


class CloseShiftRequest(BaseModel):
    close_type: int = 0


@router.get("/active")
async def active_shift(
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    shift = await get_active_shift(db)
    if not shift:
        return {"active": False, "shift": None}
    return {"active": True, "shift": _shift_dict(shift)}


@router.post("/open")
async def shift_open(
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    trk = get_trk_driver()
    # Barcha pistoletlar uchun boshlang'ich counter olish
    statuses = await trk.get_all_statuses()
    counters = {s.pist_id: s.counter for s in statuses}

    try:
        shift = await open_shift(db, op.OperatorID, counters=counters)
    except ShiftError as e:
        raise HTTPException(400, str(e))

    return {"success": True, "shift": _shift_dict(shift)}


@router.post("/{shift_id}/close")
async def shift_close(
    shift_id: int,
    req: CloseShiftRequest,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    trk = get_trk_driver()
    statuses = await trk.get_all_statuses()
    end_counters = {s.pist_id: s.counter for s in statuses}

    try:
        shift = await close_shift(db, shift_id, op.OperatorID, req.close_type, end_counters)
    except ShiftError as e:
        raise HTTPException(400, str(e))

    summary = await get_shift_summary(db, shift_id)
    return {"success": True, "shift": _shift_dict(shift), "summary": summary}


@router.get("/{shift_id}/summary")
async def shift_summary(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    return await get_shift_summary(db, shift_id)


@router.get("")
async def list_shifts(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    rows = (await db.execute(
        select(Change).order_by(Change.ChangeID.desc()).limit(limit)
    )).scalars().all()
    return [_shift_dict(r) for r in rows]


def _shift_dict(s: Change) -> dict:
    return {
        "change_id": s.ChangeID,
        "start": s.StartDateTime.isoformat() if s.StartDateTime else None,
        "end": s.EndDateTime.isoformat() if s.EndDateTime else None,
        "operator_id": s.OperatorID,
        "closed": s.ClosedFlag,
        "close_type": s.CloseType,
    }
