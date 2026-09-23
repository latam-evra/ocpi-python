"""Módulo CDRs (mod_cdrs), implementado server-side en el Hub.

Field shapes mirror lib/ocpi/cdrs.ts (toPublicCdr / cdrInputSchema). CDRs
son inmutables: solo POST (creación) y GET, sin PUT/PATCH/DELETE.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from .sessions import AuthMethod, CdrToken, ChargingPeriod, CostAmount

__all__ = [
    "AuthMethod",
    "CdrToken",
    "ChargingPeriod",
    "CostAmount",
    "GeoLocation",
    "ConnectorFormat",
    "ConnectorPowerType",
    "CdrLocation",
    "PriceComponent",
    "CdrTariffElement",
    "CdrTariff",
    "CdrInput",
    "Cdr",
    "CdrsPage",
]


class GeoLocation(BaseModel):
    latitude: str
    longitude: str


class ConnectorFormat(str, Enum):
    SOCKET = "SOCKET"
    CABLE = "CABLE"


class ConnectorPowerType(str, Enum):
    AC_1_PHASE = "AC_1_PHASE"
    AC_2_PHASE = "AC_2_PHASE"
    AC_2_PHASE_SPLIT = "AC_2_PHASE_SPLIT"
    AC_3_PHASE = "AC_3_PHASE"
    DC = "DC"


class CdrLocation(BaseModel):
    id: str
    name: str | None = None
    address: str
    city: str
    postal_code: str | None = None
    country: str
    coordinates: GeoLocation
    evse_id: str | None = None
    evse_uid: str
    connector_id: str
    connector_standard: str
    connector_format: ConnectorFormat
    connector_power_type: ConnectorPowerType


class PriceComponent(BaseModel):
    type: str
    price: float
    vat: float | None = None
    step_size: int


class CdrTariffElement(BaseModel):
    price_components: list[PriceComponent]
    restrictions: dict | None = None


class CdrTariff(BaseModel):
    """Tariff embebido en un CDR — shape propio con ``elements``, distinto
    de ``Tariff`` (models/tariffs.py), que es el recurso independiente del
    módulo Tariffs."""

    country_code: str
    party_id: str
    id: str
    currency: str
    elements: list[CdrTariffElement]


class CdrInput(BaseModel):
    id: str
    start_date_time: str
    end_date_time: str
    session_id: str | None = None
    cdr_token: CdrToken
    auth_method: AuthMethod
    authorization_reference: str | None = None
    cdr_location: CdrLocation
    meter_id: str | None = None
    currency: str
    tariffs: list[CdrTariff] | None = None
    charging_periods: list[ChargingPeriod]
    signed_data: dict | None = None
    total_cost: CostAmount
    total_fixed_cost: CostAmount | None = None
    total_energy: float
    total_energy_cost: CostAmount | None = None
    total_time: float
    total_time_cost: CostAmount | None = None
    total_parking_time: float | None = None
    total_parking_cost: CostAmount | None = None
    total_reservation_cost: CostAmount | None = None
    remark: str | None = None
    invoice_reference_id: str | None = None
    credit: bool | None = None
    credit_reference_id: str | None = None


class Cdr(CdrInput):
    country_code: str
    party_id: str
    last_updated: str


class CdrsPage(BaseModel):
    cdrs: list[Cdr]
    total: int
