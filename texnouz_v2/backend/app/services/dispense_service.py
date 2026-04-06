"""Gaz quyish jarayoni — buyurtma, nazorat, yakunlash"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import MainData
from app.models.fuel import GasType, Storage
from app.services.shift_service import get_active_shift
from app.services.payment_service import apply_discount

# OperationID konstantalari (tabOperation dagi qiymatlar)
OP_FUEL_CASH = 1       # naqd gaz sotish
OP_FUEL_BANK = 2       # bank kartasi bilan
OP_FUEL_TALON = 3      # talon bilan
OP_FUEL_PARTNER = 4    # hamkor debeti bilan
OP_FUEL_CARD = 5       # smart karta bilan
OP_GOODS_CASH = 6      # tovar naqd
OP_GOODS_BANK = 7      # tovar bank
OP_PARTNER_IN = 8      # hamkor to'lov kirim

# EndCode konstantalari
END_OK = 0
END_ARMED = 1
END_DISPENSING = 2
END_COMPLETE = 3
END_ERROR = 99


class DispenseError(Exception):
    pass


async def create_order(
    db: AsyncSession,
    *,
    operator_id: int,
    pistolet_id: int,
    gas_id: int,
    cistern_id: int,
    preset_liters: float | None = None,    # litr (float)
    preset_money: float | None = None,
    payment_type: str = "cash",            # cash | bank | talon | partner | card
    partner_id: int | None = None,
    card_number: str | None = None,
    car_number: str | None = None,
) -> MainData:
    """
    Yangi gaz quyish buyurtmasi yaratish.
    TRK qurilmaga arm buyrugi hardware moduldan yuboriladi.
    """
    shift = await get_active_shift(db)
    if not shift:
        raise DispenseError("Faol smena yo'q — avval smenani oching")

    # Gaz narxi va chegirma
    gas = (await db.execute(select(GasType).where(GasType.GasID == gas_id))).scalar_one_or_none()
    if not gas:
        raise DispenseError(f"Gaz turi topilmadi: {gas_id}")

    price = gas.Price
    discount1 = gas.Discount1
    discount2 = gas.Discount2

    order_liters_int = int((preset_liters or 0) * 100)
    order_money = Decimal(str(preset_money or 0))

    op_id = {
        "cash": OP_FUEL_CASH,
        "bank": OP_FUEL_BANK,
        "talon": OP_FUEL_TALON,
        "partner": OP_FUEL_PARTNER,
        "card": OP_FUEL_CARD,
    }.get(payment_type, OP_FUEL_CASH)

    row = MainData(
        ChangeID=shift.ChangeID,
        GasID=gas_id,
        GasMetan=gas.GasMetan,
        CisternID=cistern_id,
        PartnerID=partner_id or 0,
        OperationID=op_id,
        PistoletID=pistolet_id,
        OrderLiters=order_liters_int,
        OrderMoney=order_money,
        Liters=0,
        Price=price,
        Discount1=discount1,
        Discount2=discount2,
        EndCode=END_ARMED,
        OperatorID=operator_id,
        DateTime=datetime.now(),
        SYNC=False,
        CarNumber=car_number,
        CardNumber=card_number,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_dispensing(db: AsyncSession, data_id: int, liters_dispensed: float) -> None:
    """TRK polling paytida real-time litr yangilash"""
    await db.execute(
        update(MainData)
        .where(MainData.DataID == data_id)
        .values(Liters=int(liters_dispensed * 100), EndCode=END_DISPENSING)
    )
    await db.commit()


async def complete_order(
    db: AsyncSession,
    data_id: int,
    *,
    liters_actual: float,
    money_cash: float = 0,
    money_bank: float = 0,
    money_talon: float = 0,
    money_fut: float = 0,
    water_level: int = 0,
    pressure: int = 0,
    dencity: int = 0,
    mass: int = 0,
    mgaslevel: int = 0,
    end_counter: int | None = None,
) -> MainData:
    """
    Gaz quyish yakunlanganidan keyin to'lovni qayd etish.
    """
    row = await db.get(MainData, data_id)
    if not row:
        raise DispenseError(f"Tranzaksiya topilmadi: {data_id}")

    liters_int = int(liters_actual * 100)
    price = row.Price

    # Chegirma hisoblanadi
    effective_price = apply_discount(price, row.Discount1, row.Discount2)
    total_sum = Decimal(str(liters_actual)) * effective_price

    row.Liters = liters_int
    row.MoneyCash = Decimal(str(money_cash))
    row.MoneyBank = Decimal(str(money_bank))
    row.MoneyTalon = Decimal(str(money_talon))
    row.MoneyFut = Decimal(str(money_fut))
    row.WaterLevel = water_level
    row.Pressure = pressure
    row.Dencity = dencity
    row.Mass = mass
    row.MGasLevel = mgaslevel
    row.EndCode = END_COMPLETE
    row.SYNC = False

    # Sisterna hajmini kamaytirish
    if row.CisternID:
        await db.execute(
            update(Storage)
            .where(Storage.CisternID == row.CisternID)
            .values(Volume=Storage.Volume - liters_int, SYNC=False)
        )

    await db.commit()
    await db.refresh(row)
    return row


async def cancel_order(db: AsyncSession, data_id: int) -> None:
    """Buyurtmani bekor qilish (TRK dan stop buyrugi yuborilgandan keyin)"""
    await db.execute(
        update(MainData)
        .where(MainData.DataID == data_id)
        .values(EndCode=END_ERROR, Liters=0, SYNC=False)
    )
    await db.commit()
