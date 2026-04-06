"""FastAPI dependency injection"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.operator import Operator
from sqlalchemy import select

bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"


async def get_current_operator(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Operator:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token kerak")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM])
        operator_id: int = payload.get("sub")
        if operator_id is None:
            raise HTTPException(status_code=401, detail="Token noto'g'ri")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token muddati o'tgan")

    op = (await db.execute(select(Operator).where(Operator.OperatorID == operator_id))).scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=401, detail="Operator topilmadi")
    return op
