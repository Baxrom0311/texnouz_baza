"""Hamkor debet/kredit hisobi"""
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import Partner, PartnerAccount, PartnerInHistory, PartnerOutHistory


class PartnerError(Exception):
    pass


async def get_balance(db: AsyncSession, partner_id: int, gas_id: int) -> dict:
    acc = (await db.execute(
        select(PartnerAccount)
        .where(PartnerAccount.PartnerID == partner_id, PartnerAccount.GasID == gas_id)
    )).scalar_one_or_none()

    if not acc:
        return {"debet": 0.0, "credit": 0.0, "debet_liters": 0.0, "credit_liters": 0.0}

    return {
        "debet": acc.Debet,
        "credit": acc.Credit,
        "debet_liters": acc.Debet / 100.0,
        "credit_liters": acc.Credit / 100.0,
    }


async def ensure_account(db: AsyncSession, partner_id: int, gas_id: int) -> PartnerAccount:
    """Hamkor hisobi yo'q bo'lsa yaratish"""
    acc = (await db.execute(
        select(PartnerAccount)
        .where(PartnerAccount.PartnerID == partner_id, PartnerAccount.GasID == gas_id)
    )).scalar_one_or_none()

    if not acc:
        acc = PartnerAccount(
            PartnerID=partner_id,
            GasID=gas_id,
            Debet=0,
            Credit=0,
            DateTime=datetime.now(),
        )
        db.add(acc)
        await db.flush()
    return acc


async def add_credit(
    db: AsyncSession,
    partner_id: int,
    gas_id: int,
    liters_x100: int,
    data_id: int,
    change_id: int,
    operator_id: int,
    card_id: int = 0,
) -> None:
    """
    Hamkorga kredit qo'shish (gaz berish).
    tabPartnerOutHistory + tabPartnerAccount.Credit += liters_x100
    """
    acc = await ensure_account(db, partner_id, gas_id)

    hist = PartnerOutHistory(
        PartnerID=partner_id,
        CardID=card_id,
        GasID=gas_id,
        DataID=data_id,
        ChangeID=change_id,
        Credit=liters_x100,
        Debet=0,
        OperatorID=operator_id,
        DateTime=datetime.now(),
    )
    db.add(hist)

    await db.execute(
        update(PartnerAccount)
        .where(PartnerAccount.DataID == acc.DataID)
        .values(Credit=PartnerAccount.Credit + liters_x100, DateTime=datetime.now())
    )
    await db.commit()


async def add_payment(
    db: AsyncSession,
    partner_id: int,
    gas_id: int,
    liters_x100: int,
    data_id: int,
    change_id: int,
    operator_id: int,
    card_id: int = 0,
) -> None:
    """
    Hamkor to'lov qildi (debet to'ldirish).
    tabPartnerInHistory + tabPartnerAccount.Debet += liters_x100
    """
    acc = await ensure_account(db, partner_id, gas_id)

    hist = PartnerInHistory(
        PartnerID=partner_id,
        CardID=card_id,
        GasID=gas_id,
        DataID=data_id,
        ChangeID=change_id,
        Debet=liters_x100,
        Credit=0,
        OperatorID=operator_id,
        DateTime=datetime.now(),
    )
    db.add(hist)

    await db.execute(
        update(PartnerAccount)
        .where(PartnerAccount.DataID == acc.DataID)
        .values(Debet=PartnerAccount.Debet + liters_x100, DateTime=datetime.now())
    )
    await db.commit()
