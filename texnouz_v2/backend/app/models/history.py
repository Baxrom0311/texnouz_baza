from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Double, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class GasHistory(Base):
    __tablename__ = "tabGasHistory"

    Cnt: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ChangeID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabChange.ChangeID"))
    CisternID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabStorage.CisternID"))
    StartGasLevel: Mapped[int] = mapped_column(Integer, default=0)
    StartWaterLevel: Mapped[int] = mapped_column(Integer, default=0)
    StartLiters: Mapped[int] = mapped_column(Integer, default=0)
    EndGasLevel: Mapped[int] = mapped_column(Integer, default=0)
    EndWaterLevel: Mapped[int] = mapped_column(Integer, default=0)
    EndLiters: Mapped[int] = mapped_column(Integer, default=0)
    AddLiters: Mapped[int] = mapped_column(Integer, default=0)   # kiritilgan litr * 100
    Date: Mapped[datetime | None] = mapped_column(DateTime)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    Density: Mapped[float | None] = mapped_column(Double)
    Temperature: Mapped[int | None] = mapped_column(Integer)
    NumAuto: Mapped[str | None] = mapped_column(String(20))
    ExpeditorName: Mapped[str | None] = mapped_column(String(50))
    SalerName: Mapped[str | None] = mapped_column(String(50))
    NumDocum: Mapped[int | None] = mapped_column(Integer)
    DateDocum: Mapped[datetime | None] = mapped_column(DateTime)
    GasMetan: Mapped[int] = mapped_column(Integer, default=0)
    SYNC: Mapped[bool] = mapped_column(Boolean, default=False)


class PriceHistory(Base):
    __tablename__ = "tabPriceHistory"

    Cnt: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GasID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabGasType.GasID"))
    Price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Discount1: Mapped[int] = mapped_column(Integer, default=0)
    Discount2: Mapped[int] = mapped_column(Integer, default=0)
    Discount3: Mapped[int] = mapped_column(Integer, default=0)
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    MTaxTypes: Mapped[str | None] = mapped_column(String(8))
