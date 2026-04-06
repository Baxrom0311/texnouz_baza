"""Smena (shift) boshqaruvi — ochish, yopish, faol smena olish"""
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift import Change
from app.models.counters import SummCounter
from app.models.transaction import MainData, MainDataHistory
from app.models.fuel import TRK


class ShiftError(Exception):
    pass


async def get_active_shift(db: AsyncSession) -> Change | None:
    result = await db.execute(
        select(Change).where(Change.ClosedFlag == False).order_by(Change.ChangeID.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def open_shift(db: AsyncSession, operator_id: int, counters: dict[int, int] | None = None) -> Change:
    """
    Yangi smena ochish.
    counters: {PistoletID: BeginCounter} — TRK schetchiklari boshlang'ich qiymatlari
    """
    active = await get_active_shift(db)
    if active:
        raise ShiftError(f"Faol smena allaqachon mavjud (ChangeID={active.ChangeID})")

    shift = Change(
        StartDateTime=datetime.now(),
        OperatorID=operator_id,
        ClosedFlag=False,
        CloseType=0,
        OpenCounter=0,
        SYNC=False,
    )
    db.add(shift)
    await db.flush()  # ChangeID generatsiya qilinadi

    # Har bir pistolet uchun SummCounters yozuvi
    if counters:
        for pist_id, begin_cnt in counters.items():
            sc = SummCounter(
                ChangeID=shift.ChangeID,
                PistNum=pist_id,
                BeginCounter=begin_cnt,
                EndCounter=begin_cnt,
                SYNC=False,
            )
            db.add(sc)

    await db.commit()
    await db.refresh(shift)
    return shift


async def close_shift(
    db: AsyncSession,
    shift_id: int,
    operator_id: int,
    close_type: int = 0,
    end_counters: dict[int, int] | None = None,
) -> Change:
    """
    Smenani yopish:
    1. tabSummCounters.EndCounter yangilanadi
    2. tabMainData → tabMainDataHistory ko'chiriladi
    3. tabChange.ClosedFlag = True
    """
    shift = await db.get(Change, shift_id)
    if not shift:
        raise ShiftError(f"Smena topilmadi: {shift_id}")
    if shift.ClosedFlag:
        raise ShiftError(f"Smena allaqachon yopilgan: {shift_id}")

    # 1. SummCounters EndCounter yangilash
    if end_counters:
        for pist_id, end_cnt in end_counters.items():
            await db.execute(
                update(SummCounter)
                .where(SummCounter.ChangeID == shift_id, SummCounter.PistNum == pist_id)
                .values(EndCounter=end_cnt, EndDateTime=datetime.now(), SYNC=False)
            )

    # 2. tabMainData → tabMainDataHistory ko'chirish
    rows = (await db.execute(
        select(MainData).where(MainData.ChangeID == shift_id)
    )).scalars().all()

    for row in rows:
        hist = MainDataHistory(
            DataID=row.DataID,
            ChangeID=row.ChangeID,
            GasID=row.GasID,
            CisternID=row.CisternID,
            PartnerID=row.PartnerID,
            OperationID=row.OperationID,
            PistoletID=row.PistoletID,
            Liters=row.Liters,
            OrderLiters=row.OrderLiters,
            MoneyCash=row.MoneyCash,
            MoneyTalon=row.MoneyTalon,
            MoneyBank=row.MoneyBank,
            MoneyFut=row.MoneyFut,
            OrderMoney=row.OrderMoney,
            Price=row.Price,
            Discount1=row.Discount1,
            Discount2=row.Discount2,
            Debet=row.Debet,
            Credit=row.Credit,
            WaterLevel=row.WaterLevel,
            EndCode=row.EndCode,
            OperatorID=row.OperatorID,
            DateTime=row.DateTime,
            CasseID=row.CasseID,
            Count=row.Count,
            Article=row.Article,
            CheckID=row.CheckID,
            Mass=row.Mass,
            Dencity=row.Dencity,
            Pressure=row.Pressure,
            Kbrd=row.Kbrd,
            SYNC=False,
            CarNumber=row.CarNumber,
            GasMetan=row.GasMetan,
            MGasLevel=row.MGasLevel,
            CardNumber=row.CardNumber,
        )
        db.add(hist)
        await db.delete(row)

    # 3. tabChange yopish
    shift.EndDateTime = datetime.now()
    shift.ClosedFlag = True
    shift.CloseType = close_type
    shift.SYNC = False

    await db.commit()
    await db.refresh(shift)
    return shift


async def get_shift_summary(db: AsyncSession, shift_id: int) -> dict:
    """Smena hisoboti uchun yig'ma ma'lumot"""
    from sqlalchemy import func
    from app.models.fuel import GasType

    # Gaz bo'yicha yig'ma
    gas_rows = (await db.execute(
        select(
            MainData.GasID,
            func.sum(MainData.Liters).label("total_liters"),
            func.sum(MainData.MoneyCash).label("cash"),
            func.sum(MainData.MoneyBank).label("bank"),
            func.sum(MainData.MoneyTalon).label("talon"),
            func.sum(MainData.MoneyFut).label("fut"),
        )
        .where(MainData.ChangeID == shift_id, MainData.GasID != None, MainData.GasID != 0)
        .group_by(MainData.GasID)
    )).all()

    # Umumiy pul
    total_row = (await db.execute(
        select(
            func.sum(MainData.MoneyCash).label("cash"),
            func.sum(MainData.MoneyBank).label("bank"),
            func.sum(MainData.MoneyTalon).label("talon"),
            func.sum(MainData.MoneyFut).label("fut"),
        )
        .where(MainData.ChangeID == shift_id)
    )).one()

    # Pistolet schetchiklari
    counters = (await db.execute(
        select(SummCounter).where(SummCounter.ChangeID == shift_id)
    )).scalars().all()

    return {
        "shift_id": shift_id,
        "gas_summary": [
            {
                "gas_id": r.GasID,
                "liters": (r.total_liters or 0) / 100.0,
                "cash": float(r.cash or 0),
                "bank": float(r.bank or 0),
                "talon": float(r.talon or 0),
                "credit": float(r.fut or 0),
            }
            for r in gas_rows
        ],
        "total_cash": float(total_row.cash or 0),
        "total_bank": float(total_row.bank or 0),
        "total_talon": float(total_row.talon or 0),
        "total_credit": float(total_row.fut or 0),
        "counters": [
            {
                "pist_num": c.PistNum,
                "begin": c.BeginCounter,
                "end": c.EndCounter,
                "dispensed": c.EndCounter - c.BeginCounter,
            }
            for c in counters
        ],
    }
