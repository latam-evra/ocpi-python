from __future__ import annotations

from pydantic import BaseModel


class PriceComponent(BaseModel):
    type: str
    price: float
    vat: float | None = None
    step_size: int


class TariffElement(BaseModel):
    price_components: list[PriceComponent]


class TariffInput(BaseModel):
    id: str
    currency: str
    elements: list[TariffElement]


class Tariff(BaseModel):
    country_code: str
    party_id: str
    id: str
    currency: str
    elements: list[TariffElement]


class TariffsPage(BaseModel):
    tariffs: list[Tariff]
    total: int
