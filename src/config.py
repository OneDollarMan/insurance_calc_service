import os
from enum import Enum

PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_HOST = os.getenv("POSTGRES_HOST")
PG_PORT = os.getenv("POSTGRES_PORT")
PG_DB = os.getenv("POSTGRES_DB")
DATABASE_URL = f'postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'
KAFKA_URL = os.getenv("KAFKA_URL")


class ActionEnum(Enum):
    RATES_UPLOADED = 'Rates uploaded'
    PRICE_CALCULATED = 'Price calculated'
    RATE_EDITED = 'Rate edited'
    RATE_DELETED = 'Rate deleted'
