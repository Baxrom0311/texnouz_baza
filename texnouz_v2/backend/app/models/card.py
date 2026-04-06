from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CardType(Base):
    __tablename__ = "tabCardTypes"

    CTNum: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CTName: Mapped[str | None] = mapped_column(String(20), unique=True)


class CardNumber(Base):
    __tablename__ = "tabCardNumbers"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CardNumber: Mapped[str | None] = mapped_column(String(20), unique=True)
    CardType: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabCardTypes.CTNum"))
    GasID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabGasType.GasID"))
    PartnerID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabPartner.PartnerID"))
    DiscSchema: Mapped[int | None] = mapped_column(Integer)
    Liters: Mapped[int] = mapped_column(Integer, default=0)   # litr limiti * 100
    EndDate: Mapped[datetime | None] = mapped_column(DateTime)
    Date: Mapped[datetime | None] = mapped_column(DateTime)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    Enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    Sold: Mapped[bool] = mapped_column(Boolean, default=False)
