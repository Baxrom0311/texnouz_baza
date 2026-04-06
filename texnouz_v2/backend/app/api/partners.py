"""Hamkorlar API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_operator
from app.database import get_db
from app.models.operator import Operator
from app.models.partner import Partner, PartnerAccount
from app.services.partner_service import get_balance

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("")
async def list_partners(
    enabled_only: bool = True,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    q = select(Partner)
    if enabled_only:
        q = q.where(Partner.Enabled == True)
    rows = (await db.execute(q.order_by(Partner.Name))).scalars().all()
    return [{"partner_id": r.PartnerID, "name": r.Name, "phone": r.Phone} for r in rows]


@router.get("/{partner_id}/balance/{gas_id}")
async def partner_balance(
    partner_id: int,
    gas_id: int,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    return await get_balance(db, partner_id, gas_id)


class CreatePartnerRequest(BaseModel):
    name: str
    address: str = ""
    phone: str = ""


@router.post("")
async def create_partner(
    req: CreatePartnerRequest,
    db: AsyncSession = Depends(get_db),
    op: Operator = Depends(get_current_operator),
):
    from datetime import datetime
    partner = Partner(
        Name=req.name,
        Address=req.address,
        Phone=req.phone,
        Enabled=True,
        DateTime=datetime.now(),
        OperatorID=op.OperatorID,
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return {"partner_id": partner.PartnerID, "name": partner.Name}
