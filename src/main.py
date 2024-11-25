import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import RatesSchema, CalculatePriceSchema, RateEditSchema, RateReadSchema, RateDeleteSchema, \
    CalculatedPriceSchema
from db import get_async_session, create_db_and_tables
from service import save_rates, calculate_price, edit_rate, delete_rate
from config import ActionEnum, KAFKA_URL
from logger import KafkaBatchLogger

logger = KafkaBatchLogger(
        bootstrap_servers=KAFKA_URL,
        topic="log_topic",
        batch_size=100,
        flush_interval=5
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    asyncio.create_task(logger.start())
    yield


app = FastAPI(lifespan=lifespan)


@app.post('/upload_rates')
async def post_upload_rates(rates: RatesSchema, s: AsyncSession = Depends(get_async_session)):
    logger.log_action(ActionEnum.RATES_UPLOADED)
    await save_rates(s, rates)


@app.post('/calculate_price', response_model=CalculatedPriceSchema)
async def post_calculate_price(calc_schema: CalculatePriceSchema, s: AsyncSession = Depends(get_async_session)) -> float:
    logger.log_action(ActionEnum.PRICE_CALCULATED)
    return await calculate_price(s, calc_schema)


@app.patch('/rate/edit', response_model=RateReadSchema)
async def patch_rate_edit(rate: RateEditSchema, s: AsyncSession = Depends(get_async_session)):
    logger.log_action(ActionEnum.RATE_EDITED)
    return await edit_rate(s, rate)


@app.delete('/rate/delete')
async def put_rate_edit(rate: RateDeleteSchema, s: AsyncSession = Depends(get_async_session)):
    logger.log_action(ActionEnum.RATE_DELETED)
    await delete_rate(s, rate)
