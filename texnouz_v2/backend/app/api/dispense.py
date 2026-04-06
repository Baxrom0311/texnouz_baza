"""Gaz quyish API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_operator
from app.database import get_db
from app.hardware.mariya.driver import get_trk_driver
from app.models.operator import Operator
from app.services.dispense_service import (
    DispenseError, cancel_order, complete_order, create_order,
)
from app.services.partner_service import add_credit

router = APIRouter(prefix="/dispense", tags=["dispense"])


class OrderRequest(BaseModel):
    pistolet_id: int
    gas_id: int
    cistern_id: int
    preset_liters: float | None = None
    preset_money: float | None = None
    payment_type: str = "cash"   # cash | bank | talon | partner | card
    partner_id: int | None = None
    card_number: str | None = None
    car_number: str | None = None


class CompleteRequest(BaseModel):
    liters_actual: float
    money_cash: float = 0
    money_bank: float = 0
    money_talon: float = 0
    money_fut: float = 0
    water_level: int = 0
    pressure: int = 0
    dencity: int = 0


@router.post("/order")
async def create(
    req: OrderRequest,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    try:
        order = await create_order(
            db,
            operator_id=op.OperatorID,
            pistolet_id=req.pistolet_id,
            gas_id=req.gas_id,
            cistern_id=req.cistern_id,
            preset_liters=req.preset_liters,
            preset_money=req.preset_money,
            payment_type=req.payment_type,
            partner_id=req.partner_id,
            card_number=req.card_number,
            car_number=req.car_number,
        )
    except DispenseError as e:
        raise HTTPException(400, str(e))

    # TRK arm
    driver = get_trk_driver()
    await driver.arm(req.pistolet_id, req.preset_liters, req.preset_money)

    return {
        "data_id": order.DataID,
        "change_id": order.ChangeID,
        "pistolet_id": order.PistoletID,
        "gas_id": order.GasID,
        "order_liters": order.order_liters_float,
        "order_money": float(order.OrderMoney),
        "price": float(order.Price),
        "end_code": order.EndCode,
    }


@router.post("/{data_id}/complete")
async def complete(
    data_id: int,
    req: CompleteRequest,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    try:
        order = await complete_order(
            db,
            data_id,
            liters_actual=req.liters_actual,
            money_cash=req.money_cash,
            money_bank=req.money_bank,
            money_talon=req.money_talon,
            money_fut=req.money_fut,
            water_level=req.water_level,
            pressure=req.pressure,
            dencity=req.dencity,
        )
    except DispenseError as e:
        raise HTTPException(400, str(e))

    # Hamkor debeti
    if order.PartnerID and order.PartnerID != 0 and order.GasID:
        await add_credit(
            db,
            partner_id=order.PartnerID,
            gas_id=order.GasID,
            liters_x100=order.Liters,
            data_id=order.DataID,
            change_id=order.ChangeID or 0,
            operator_id=op.OperatorID,
        )

    # Chek chiqarish
    from app.hardware.shtrih.driver import get_shtrih_driver
    printer = get_shtrih_driver()
    payment_type = 1  # naqd default
    if req.money_bank > 0:
        payment_type = 2
    elif req.money_talon > 0:
        payment_type = 3

    await printer.print_fuel_receipt(
        receipt_num=order.CheckID or order.DataID,
        operator_name="",
        gas_name=f"Gaz #{order.GasID}",
        liters=order.liters_float,
        price=float(order.Price),
        total=float(order.MoneyCash + order.MoneyBank + order.MoneyTalon + order.MoneyFut),
        payment_type=payment_type,
    )

    return {
        "data_id": order.DataID,
        "liters": order.liters_float,
        "money_cash": float(order.MoneyCash),
        "money_bank": float(order.MoneyBank),
        "money_talon": float(order.MoneyTalon),
        "end_code": order.EndCode,
    }


@router.post("/{data_id}/cancel")
async def cancel(
    data_id: int,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    order = await db.get(__import__("app.models.transaction", fromlist=["MainData"]).MainData, data_id)
    if order:
        driver = get_trk_driver()
        await driver.stop(order.PistoletID)
    await cancel_order(db, data_id)
    return {"success": True}
