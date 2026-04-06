from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OperatorType(Base):
    __tablename__ = "tabOperatorType"

    TypeID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    TypeName: Mapped[str | None] = mapped_column(String(15))

    operators: Mapped[list["Operator"]] = relationship(back_populates="type_rel")


class Operator(Base):
    __tablename__ = "tabOperator"

    OperatorID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    AZSID: Mapped[int | None] = mapped_column(Integer)
    Name: Mapped[str | None] = mapped_column(String(50))
    Password: Mapped[str | None] = mapped_column(String(10), unique=True)
    Address: Mapped[str | None] = mapped_column(String(50))
    Phone: Mapped[str | None] = mapped_column(String(50))
    Date: Mapped[datetime | None] = mapped_column(DateTime)
    Type: Mapped[int | None] = mapped_column(Integer, ForeignKey("tabOperatorType.TypeID"))

    type_rel: Mapped["OperatorType | None"] = relationship(back_populates="operators")
