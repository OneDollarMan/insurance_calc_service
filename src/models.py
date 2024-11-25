from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    ...


class RateDate(Base):
    __tablename__ = 'rate_date'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, unique=True)

    rates: Mapped[list['Rate']] = relationship('Rate', back_populates='rate_date')


class Rate(Base):
    __tablename__ = 'rate'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rate_date_id: Mapped[int] = mapped_column(ForeignKey('rate_date.id'))
    cargo_type: Mapped[str] = mapped_column(Text)
    rate: Mapped[float] = mapped_column(Float)

    rate_date: Mapped[RateDate] = relationship('RateDate', back_populates='rates')
