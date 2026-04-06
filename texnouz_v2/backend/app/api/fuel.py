"""Gaz turlari va sisternalar API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_operator
from app.database import get_db
from app.models.fuel import GasType, Storage, TRK
from app.models.operator import Operator

router = APIRouter(prefix="/fuel", tags=["fuel"])


@router.get("/types")
async def get_fuel_types(db: AsyncSession = Depends(get_db), op: Operator = Depends(get_current_operator)):
    rows = (await db.execute(select(GasType).order_by(GasType.GasID))).scalars().all()
    return [
        {
            "gas_id": r.GasID,
            "name": r.GasName,
            "check_name": r.CheckName,
            "price": float(r.Price),
            "discount1": r.Discount1,
            "discount2": r.Discount2,
            "is_metan": bool(r.GasMetan),
        }
        for r in rows
    ]


@router.get("/storage")
async def get_storage(db: AsyncSession = Depends(get_db), op: Operator = Depends(get_current_operator)):
    rows = (await db.execute(select(Storage).order_by(Storage.CisternID))).scalars().all()
    return [
        {
            "cistern_id": r.CisternID,
            "gas_id": r.GasID,
            "volume": r.Volume,
            "volume_liters": r.Volume / 100.0,
        }
        for r in rows
    ]


@router.get("/trk")
async def get_trk_config(db: AsyncSession = Depends(get_db), op: Operator = Depends(get_current_operator)):
    rows = (await db.execute(select(TRK).order_by(TRK.PistoletID))).scalars().all()
    return [
        {
            "index": r.Index_,
            "trk_id": r.TRKID,
            "cistern_id": r.CisternID,
            "pistolet_id": r.PistoletID,
            "port": r.MPort,
            "baud": r.MBaud,
        }
        for r in rows
    ]


class UpdatePriceRequest(BaseModel):
    gas_id: int
    price: float


@router.post("/price")
async def update_price(
    req: UpdatePriceRequest,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    from decimal import Decimal
    from datetime import datetime
    from app.models.history import PriceHistory

    gas = (await db.execute(select(GasType).where(GasType.GasID == req.gas_id))).scalar_one_or_none()
    if not gas:
        raise HTTPException(404, "Gaz turi topilmadi")

    # Tarix saqlash
    hist = PriceHistory(
        GasID=req.gas_id,
        Price=Decimal(str(gas.Price)),
        Discount1=gas.Discount1,
        Discount2=gas.Discount2,
        Discount3=gas.Discount3,
        DateTime=datetime.now(),
        OperatorID=op.OperatorID,
    )
    db.add(hist)

    gas.Price = Decimal(str(req.price))
    await db.commit()
    return {"success": True, "gas_id": req.gas_id, "new_price": req.price}
