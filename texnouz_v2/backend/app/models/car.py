from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CarPassport(Base):
    __tablename__ = "tabCarPassport"

    CarID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    TalonNumber: Mapped[str | None] = mapped_column(String(12))
    CarNumber: Mapped[str | None] = mapped_column(String(12), unique=True)
    CarType: Mapped[str | None] = mapped_column(String(10))
    BalloonNum: Mapped[int | None] = mapped_column(Integer)
    FirmName: Mapped[str | None] = mapped_column(String(50))
    EndDate: Mapped[datetime | None] = mapped_column(DateTime)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    SYNC: Mapped[bool] = mapped_column(Boolean, default=False)
