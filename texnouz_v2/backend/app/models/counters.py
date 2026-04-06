from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SummCounter(Base):
    __tablename__ = "tabSummCounters"

    DataID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ChangeID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabChange.ChangeID"), index=True)
    PistNum: Mapped[int | None] = mapped_column(Integer)
    EndDateTime: Mapped[datetime | None] = mapped_column(DateTime)
    BeginCounter: Mapped[int] = mapped_column(BigInteger, default=0)
    EndCounter: Mapped[int] = mapped_column(BigInteger, default=0)
    SYNC: Mapped[bool] = mapped_column(Boolean, default=False)
