from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Change(Base):
    __tablename__ = "tabChange"

    ChangeID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    StartDateTime: Mapped[datetime | None] = mapped_column(DateTime)
    EndDateTime: Mapped[datetime | None] = mapped_column(DateTime)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    ClosedFlag: Mapped[bool] = mapped_column(Boolean, default=False)
    CloseType: Mapped[int] = mapped_column(Integer, default=0)
    OpenCounter: Mapped[int] = mapped_column(Integer, default=0)
    SYNC: Mapped[bool] = mapped_column(Boolean, default=False)
