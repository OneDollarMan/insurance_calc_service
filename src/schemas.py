from datetime import date
from typing import List, Dict
from pydantic import BaseModel, RootModel, field_validator


class RateCreateSchema(BaseModel):
    cargo_type: str
    rate: float


class RateReadSchema(BaseModel):
    id: int
    cargo_type: str
    rate: float


class RateEditSchema(BaseModel):
    date: date
    cargo_type: str
    rate: float


class RateDeleteSchema(BaseModel):
    date: date
    cargo_type: str


class RatesSchema(RootModel[Dict[date, List[RateCreateSchema]]]):
    ...


class CalculatePriceSchema(BaseModel):
    declared_value: float
    cargo_type: str
    date: date


class CalculatedPriceSchema(BaseModel):
    price: float
