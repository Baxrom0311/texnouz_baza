"""TRK holati va nazorat API"""
import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_operator
from app.database import get_db
from app.hardware.mariya.driver import get_trk_driver
from app.models.operator import Operator

router = APIRouter(prefix="/trk", tags=["trk"])


@router.get("/status")
async def get_status(op: Operator = Depends(get_current_operator)):
    driver = get_trk_driver()
    statuses = await driver.get_all_statuses()
    return [
        {
            "pist_id": s.pist_id,
            "status": s.status,
            "status_name": s.status_name,
            "liters": round(s.liters, 2),
            "counter": s.counter,
        }
        for s in statuses
    ]


@router.get("/events")
async def sse_events(op: Operator = Depends(get_current_operator)):
    """
    Server-Sent Events — frontend har 1 soniyada TRK holatini oladi.
    """
    async def generate() -> AsyncGenerator[str, None]:
        driver = get_trk_driver()
        while True:
            try:
                statuses = await driver.get_all_statuses()
                data = [
                    {
                        "pist_id": s.pist_id,
                        "status": s.status,
                        "status_name": s.status_name,
                        "liters": round(s.liters, 2),
                        "counter": s.counter,
                    }
                    for s in statuses
                ]
                yield f"data: {json.dumps(data)}\n\n"
            except Exception:
                yield "data: []\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(generate(), media_type="text/event-stream")


class ArmRequest(BaseModel):
    pist_id: int
    preset_liters: float | None = None
    preset_money: float | None = None


@router.post("/arm")
async def arm_gun(req: ArmRequest, op: Operator = Depends(get_current_operator)):
    driver = get_trk_driver()
    ok = await driver.arm(req.pist_id, req.preset_liters, req.preset_money)
    return {"success": ok, "pist_id": req.pist_id}


@router.post("/stop/{pist_id}")
async def stop_gun(pist_id: int, op: Operator = Depends(get_current_operator)):
    driver = get_trk_driver()
    liters = await driver.stop(pist_id)
    return {"success": True, "pist_id": pist_id, "liters_stopped": round(liters, 2)}
