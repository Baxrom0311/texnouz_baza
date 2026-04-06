"""Operator login"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ALGORITHM
from app.config import settings
from app.database import get_db
from app.models.operator import Operator

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    operator_id: int
    name: str
    type: int | None


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    op = (await db.execute(
        select(Operator).where(Operator.Password == req.password)
    )).scalar_one_or_none()

    if not op:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri")

    expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": op.OperatorID, "exp": expire},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return LoginResponse(
        token=token,
        operator_id=op.OperatorID,
        name=op.Name or "",
        type=op.Type,
    )
