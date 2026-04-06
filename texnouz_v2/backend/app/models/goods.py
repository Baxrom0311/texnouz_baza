from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Goods(Base):
    __tablename__ = "tabGoods"

    GoodsID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Article: Mapped[int | None] = mapped_column(Integer, unique=True)
    Divided: Mapped[bool] = mapped_column(Boolean, default=False)
    Enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    Taxes: Mapped[str | None] = mapped_column(String(8))
    Name: Mapped[str | None] = mapped_column(String(43))
    BarCode: Mapped[str | None] = mapped_column(String(13), unique=True)
    Price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Discount: Mapped[int] = mapped_column(Integer, default=0)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)


class GoodsHistory(Base):
    __tablename__ = "tabGoodsHistory"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GoodsID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabGoods.GoodsID"))
    Article: Mapped[int | None] = mapped_column(Integer)
    Divided: Mapped[bool | None] = mapped_column(Boolean)
    Amount: Mapped[int | None] = mapped_column(Integer)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    ChangeID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabChange.ChangeID"))
    Comment: Mapped[str | None] = mapped_column(String(100))
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)


class GoodsPriceHistory(Base):
    __tablename__ = "tabGoodsPriceHistory"

    Num: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GoodsID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabGoods.GoodsID"))
    Article: Mapped[int | None] = mapped_column(Integer)
    Divided: Mapped[bool | None] = mapped_column(Boolean)
    Enabled: Mapped[bool | None] = mapped_column(Boolean)
    Price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    Discount: Mapped[int] = mapped_column(Integer, default=0)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    ChangeID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabChange.ChangeID"))
    Comment: Mapped[str | None] = mapped_column(String(100))
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)
