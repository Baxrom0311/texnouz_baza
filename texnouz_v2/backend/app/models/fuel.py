from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class GasType(Base):
    __tablename__ = "tabGasType"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GasID: Mapped[int | None] = mapped_column(Integer, unique=True)
    GasName: Mapped[str | None] = mapped_column(String(50))
    CheckName: Mapped[str | None] = mapped_column(String(50))
    Price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Discount1: Mapped[int] = mapped_column(Integer, default=0)
    Discount2: Mapped[int] = mapped_column(Integer, default=0)
    Discount3: Mapped[int] = mapped_column(Integer, default=0)
    MTaxTypes: Mapped[str | None] = mapped_column(String(8))
    Dencity: Mapped[int | None] = mapped_column(Integer)
    GasMetan: Mapped[int] = mapped_column(Integer, default=0)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)


class Storage(Base):
    __tablename__ = "tabStorage"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CisternID: Mapped[int | None] = mapped_column(Integer, unique=True)
    GasID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabGasType.GasID"))
    Volume: Mapped[int] = mapped_column(Integer, default=0)
    Date: Mapped[datetime | None] = mapped_column(DateTime)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    SYNC: Mapped[bool] = mapped_column(Boolean, default=False)


class TRK(Base):
    __tablename__ = "tabTRK"

    Index_: Mapped[int] = mapped_column("Index", Integer, primary_key=True, autoincrement=True)
    TRKID: Mapped[int | None] = mapped_column(Integer)
    CisternID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabStorage.CisternID"))
    PistoletID: Mapped[int | None] = mapped_column(Integer)
    Half: Mapped[int | None] = mapped_column(Integer)
    HorPos: Mapped[int | None] = mapped_column(Integer)
    VerPos: Mapped[int | None] = mapped_column(Integer)
    MPort: Mapped[int | None] = mapped_column(Integer)
    MBaud: Mapped[int | None] = mapped_column(Integer)
    MUseCnt: Mapped[bool] = mapped_column(Boolean, default=False)
    MUseAvaP: Mapped[bool] = mapped_column(Boolean, default=False)
    MImpuls: Mapped[str | None] = mapped_column(String(50))
    MMaxCnt: Mapped[str | None] = mapped_column(String(50))


class LevelMeter(Base):
    __tablename__ = "tabLevelMeters"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CisternID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabStorage.CisternID"))
    LevMetType: Mapped[int | None] = mapped_column(Integer)
    SerialNum: Mapped[str | None] = mapped_column(String(20))
    LMName: Mapped[str | None] = mapped_column(String(20))
    ZeroOffset: Mapped[int] = mapped_column(Integer, default=0)
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)
