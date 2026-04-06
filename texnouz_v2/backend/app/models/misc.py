from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Operation(Base):
    __tablename__ = "tabOperation"

    OperationID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str | None] = mapped_column(String(50))


class Error(Base):
    __tablename__ = "tabErrors"

    CodeID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ErrorName: Mapped[str | None] = mapped_column(String(50))


class Tax(Base):
    __tablename__ = "tabTaxes"

    TaxID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str | None] = mapped_column(String(10))
    Percent: Mapped[int | None] = mapped_column(Integer)
    TaxType: Mapped[int | None] = mapped_column(Integer)
    OperatorID: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperator.OperatorID"))
    DateTime: Mapped[datetime | None] = mapped_column(DateTime)


class TaxType(Base):
    __tablename__ = "tabTaxsTypes"

    TTID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str | None] = mapped_column(String(20))


class Schema(Base):
    __tablename__ = "tabSchema"

    SCHID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SchName: Mapped[str | None] = mapped_column(String(200))
    SchData: Mapped[str | None] = mapped_column(String(200))


class Version(Base):
    __tablename__ = "tabVersion"

    Cnt: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    AZSID: Mapped[int | None] = mapped_column(Integer)
    VersionRelease: Mapped[int] = mapped_column(Integer, default=0)
    VersionMajor: Mapped[int] = mapped_column(Integer, default=2)
    VersionMinor: Mapped[int] = mapped_column(Integer, default=0)
