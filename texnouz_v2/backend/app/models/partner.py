from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Partner(Base):
    __tablename__ = "tabPartner"

    PartnerID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str | None] = mapped_column(String(50))
    Address: Mapped[str | None] = mapped_column(String(50))
    Phone: Mapped[str | None] = mapped_column(String(50))
    Enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))


class PartnerAccount(Base):
    __tablename__ = "tabPartnerAccount"

    DataID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    PartnerID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabPartner.PartnerID"))
    GasID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabGasType.GasID"))
    Debet: Mapped[int] = mapped_column(Integer, default=0)    # liters * 100
    Credit: Mapped[int] = mapped_column(Integer, default=0)   # liters * 100
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)


class PartnerInHistory(Base):
    __tablename__ = "tabPartnerInHistory"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    PartnerID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabPartner.PartnerID"))
    CardID: Mapped[int | None] = mapped_column(Integer)
    GasID: Mapped[int | None] = mapped_column(Integer)
    DataID: Mapped[int | None] = mapped_column(Integer)
    ChangeID: Mapped[int | None] = mapped_column(Integer)
    Debet: Mapped[int] = mapped_column(Integer, default=0)
    Credit: Mapped[int] = mapped_column(Integer, default=0)
    OperatorID: Mapped[int | None] = mapped_column(Integer)
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)


class PartnerOutHistory(Base):
    __tablename__ = "tabPartnerOutHistory"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    PartnerID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabPartner.PartnerID"))
    CardID: Mapped[int | None] = mapped_column(Integer)
    GasID: Mapped[int | None] = mapped_column(Integer)
    DataID: Mapped[int | None] = mapped_column(Integer)
    ChangeID: Mapped[int | None] = mapped_column(Integer)
    Debet: Mapped[int] = mapped_column(Integer, default=0)
    Credit: Mapped[int] = mapped_column(Integer, default=0)
    OperatorID: Mapped[int | None] = mapped_column(Integer)
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)
