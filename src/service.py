from datetime import date
from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import RatesSchema, CalculatePriceSchema, RateEditSchema, RateDeleteSchema, CalculatedPriceSchema
from models import RateDate, Rate


async def get_rate_date(s: AsyncSession, date_val: date) -> RateDate:
    rate_date = await s.execute(select(RateDate).filter(RateDate.date == date_val).limit(1))
    rate_date = rate_date.scalar()
    if not rate_date:
        raise HTTPException(status_code=404, detail=f'Not found rate date for {date_val}')
    return rate_date


async def get_rate(s: AsyncSession, rate_date_id: int, cargo_type: str) -> Rate:
    rate = await s.execute(
        select(Rate).filter(
            Rate.rate_date_id == rate_date_id,
            Rate.cargo_type == cargo_type
        ).limit(1)
    )
    rate = rate.scalar()
    if not rate:
        raise HTTPException(status_code=404, detail=f'Not found rate for {cargo_type=}')
    return rate


async def save_rates(s: AsyncSession, rates: RatesSchema):
    for date, cargo_types in rates.root.items():
        rate_date = await s.execute(select(RateDate).filter(RateDate.date == date).limit(1))
        rate_date = rate_date.scalar()
        if rate_date:
            await s.execute(delete(Rate).filter(Rate.rate_date_id == rate_date.id))
        else:
            rate_date = RateDate(date=date)
            s.add(rate_date)

        for cargo_type_data in cargo_types:
            cargo_type = Rate(rate_date=rate_date, cargo_type=cargo_type_data.cargo_type, rate=cargo_type_data.rate)
            s.add(cargo_type)

    await s.commit()


async def edit_rate(s: AsyncSession, rate_schema: RateEditSchema) -> Rate:
    rate_date = await get_rate_date(s, rate_schema.date)
    rate = await get_rate(s, rate_date.id, rate_schema.cargo_type)
    rate.rate = rate_schema.rate
    await s.commit()
    await s.refresh(rate)
    return rate


async def delete_rate(s: AsyncSession, rate_schema: RateDeleteSchema):
    rate_date = await get_rate_date(s, rate_schema.date)
    rate = await get_rate(s, rate_date.id, rate_schema.cargo_type)
    await s.delete(rate)
    await s.commit()


async def calculate_price(s: AsyncSession, calc_schema: CalculatePriceSchema) -> float:
    rate_date = await get_rate_date(s, calc_schema.date)
    rate = await get_rate(s, rate_date.id, calc_schema.cargo_type)
    return CalculatedPriceSchema(price=rate.rate * calc_schema.declared_value)
