"""Hisobotlar API"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_operator
from app.database import get_db
from app.models.operator import Operator
from app.models.transaction import MainData, MainDataHistory
from app.models.counters import SummCounter
from app.models.shift import Change
from app.services.shift_service import get_shift_summary

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/shift/{shift_id}")
async def shift_report(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    return await get_shift_summary(db, shift_id)


@router.get("/current")
async def current_shift_report(
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    from app.services.shift_service import get_active_shift
    shift = await get_active_shift(db)
    if not shift:
        return {"error": "Faol smena yo'q"}
    return await get_shift_summary(db, shift.ChangeID)


@router.get("/daily")
async def daily_report(
    date: str,  # YYYY-MM-DD
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    """Kunlik hisobot — barcha smenalarni jamlash"""
    from datetime import datetime
    try:
        day_start = datetime.strptime(date, "%Y-%m-%d")
        from datetime import timedelta
        day_end = day_start + timedelta(days=1)
    except ValueError:
        return {"error": "Sana formati: YYYY-MM-DD"}

    # Faol + yopilgan smenalar
    gas_rows = (await db.execute(
        select(
            MainData.GasID,
            func.sum(MainData.Liters).label("liters"),
            func.sum(MainData.MoneyCash).label("cash"),
            func.sum(MainData.MoneyBank).label("bank"),
            func.sum(MainData.MoneyTalon).label("talon"),
            func.sum(MainData.MoneyFut).label("fut"),
        )
        .where(
            MainData.DateTime >= day_start,
            MainData.DateTime < day_end,
            MainData.GasID != None,
        )
        .group_by(MainData.GasID)
    )).all()

    # Arxivdan ham
    hist_rows = (await db.execute(
        select(
            MainDataHistory.GasID,
            func.sum(MainDataHistory.Liters).label("liters"),
            func.sum(MainDataHistory.MoneyCash).label("cash"),
            func.sum(MainDataHistory.MoneyBank).label("bank"),
            func.sum(MainDataHistory.MoneyTalon).label("talon"),
            func.sum(MainDataHistory.MoneyFut).label("fut"),
        )
        .where(
            MainDataHistory.DateTime >= day_start,
            MainDataHistory.DateTime < day_end,
            MainDataHistory.GasID != None,
        )
        .group_by(MainDataHistory.GasID)
    )).all()

    # Merge
    totals: dict[int, dict] = {}
    for rows in [gas_rows, hist_rows]:
        for r in rows:
            gid = r.GasID or 0
            if gid not in totals:
                totals[gid] = {"gas_id": gid, "liters": 0.0, "cash": 0.0, "bank": 0.0, "talon": 0.0, "credit": 0.0}
            totals[gid]["liters"] += (r.liters or 0) / 100.0
            totals[gid]["cash"] += float(r.cash or 0)
            totals[gid]["bank"] += float(r.bank or 0)
            totals[gid]["talon"] += float(r.talon or 0)
            totals[gid]["credit"] += float(r.fut or 0)

    return {
        "date": date,
        "gas_summary": list(totals.values()),
        "grand_total": sum(
            v["cash"] + v["bank"] + v["talon"] + v["credit"] for v in totals.values()
        ),
    }
