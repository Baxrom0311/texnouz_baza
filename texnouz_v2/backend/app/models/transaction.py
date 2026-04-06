from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class MainData(Base):
    __tablename__ = "tabMainData"

    DataID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ChangeID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabChange.ChangeID"), index=True)
    GasID: Mapped[int | None] = mapped_column(Integer)
    CisternID: Mapped[int | None] = mapped_column(Integer)
    PartnerID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabPartner.PartnerID"), index=True)
    OperationID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperation.OperationID"))
    PistoletID: Mapped[int | None] = mapped_column(Integer, index=True)
    Liters: Mapped[int] = mapped_column(Integer, default=0)        # * 100 (1 litr = 100)
    OrderLiters: Mapped[int] = mapped_column(Integer, default=0)   # * 100
    MoneyCash: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    MoneyTalon: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    MoneyBank: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    MoneyFut: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    OrderMoney: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Discount1: Mapped[int] = mapped_column(Integer, default=0)
    Discount2: Mapped[int] = mapped_column(Integer, default=0)
    Debet: Mapped[int] = mapped_column(Integer, default=0)
    Credit: Mapped[int] = mapped_column(Integer, default=0)
    WaterLevel: Mapped[int] = mapped_column(Integer, default=0)
    EndCode: Mapped[int] = mapped_column(Integer, default=0)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    DateTime: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    CasseID: Mapped[int | None] = mapped_column(Integer)
    Count: Mapped[int] = mapped_column(Integer, default=0)
    Article: Mapped[int | None] = mapped_column(Integer)
    CheckID: Mapped[int | None] = mapped_column(Integer)
    Mass: Mapped[int] = mapped_column(Integer, default=0)
    Dencity: Mapped[int] = mapped_column(Integer, default=0)
    Pressure: Mapped[int] = mapped_column(Integer, default=0)
    Kbrd: Mapped[bool] = mapped_column(Boolean, default=False)
    SYNC: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    CarNumber: Mapped[str | None] = mapped_column(String(12))
    GasMetan: Mapped[int] = mapped_column(Integer, default=0)
    MGasLevel: Mapped[int] = mapped_column(Integer, default=0)
    CardNumber: Mapped[str | None] = mapped_column(String(20))

    @property
    def liters_float(self) -> float:
        return self.Liters / 100.0

    @property
    def order_liters_float(self) -> float:
        return self.OrderLiters / 100.0


class MainDataHistory(Base):
    __tablename__ = "tabMainDataHistory"

    # arxiv — PK yo'q, DataID original ID
    DataID: Mapped[int] = mapped_column(Integer, primary_key=True)
    ChangeID: Mapped[int | None] = mapped_column(Integer)
    GasID: Mapped[int | None] = mapped_column(Integer)
    CisternID: Mapped[int | None] = mapped_column(Integer)
    PartnerID: Mapped[int | None] = mapped_column(Integer)
    OperationID: Mapped[int | None] = mapped_column(Integer)
    PistoletID: Mapped[int | None] = mapped_column(Integer)
    Liters: Mapped[int] = mapped_column(Integer, default=0)
    OrderLiters: Mapped[int] = mapped_column(Integer, default=0)
    MoneyCash: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    MoneyTalon: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    MoneyBank: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    MoneyFut: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    OrderMoney: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Discount1: Mapped[int] = mapped_column(Integer, default=0)
    Discount2: Mapped[int] = mapped_column(Integer, default=0)
    Debet: Mapped[int] = mapped_column(Integer, default=0)
    Credit: Mapped[int] = mapped_column(Integer, default=0)
    WaterLevel: Mapped[int] = mapped_column(Integer, default=0)
    EndCode: Mapped[int] = mapped_column(Integer, default=0)
    OperatorID: Mapped[int | None] = mapped_column(Integer)
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)
    CasseID: Mapped[int | None] = mapped_column(Integer)
    Count: Mapped[int] = mapped_column(Integer, default=0)
    Article: Mapped[int | None] = mapped_column(Integer)
    CheckID: Mapped[int | None] = mapped_column(Integer)
    Mass: Mapped[int] = mapped_column(Integer, default=0)
    Dencity: Mapped[int] = mapped_column(Integer, default=0)
    Pressure: Mapped[int] = mapped_column(Integer, default=0)
    Kbrd: Mapped[bool] = mapped_column(Boolean, default=False)
    SYNC: Mapped[bool] = mapped_column(Boolean, default=False)
    CarNumber: Mapped[str | None] = mapped_column(String(12))
    GasMetan: Mapped[int] = mapped_column(Integer, default=0)
    MGasLevel: Mapped[int] = mapped_column(Integer, default=0)
    CardNumber: Mapped[str | None] = mapped_column(String(20))
