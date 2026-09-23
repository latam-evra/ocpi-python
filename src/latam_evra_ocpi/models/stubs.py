"""Modelos tipados para los módulos OCPI que están en el roadmap del Hub.

Ninguno de estos módulos está implementado server-side todavía (ver
``docs/Roaming_hub_Latam.md`` y ``components/ModuleAccordion.tsx``). Los
modelos se definen igual, a partir de los payloads de ejemplo publicados en
``ModuleAccordion.tsx`` y de ``docs/object_ocpi_cdr.md`` (para CDRs), para que
el tipado del SDK esté listo apenas el backend exista. Los métodos del
cliente que los usan lanzan ``OcpiModuleNotAvailableError``
(subclase de ``NotImplementedError``).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .tariffs import Tariff, TariffElement

# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    INVALID = "INVALID"
    PENDING = "PENDING"
    RESERVATION = "RESERVATION"


class Session(BaseModel):
    """Módulo Sessions — eventos de carga activos en tiempo real."""

    model_config = ConfigDict(extra="allow")

    id: str
    start_date_time: datetime
    kwh: float
    status: SessionStatus


# ---------------------------------------------------------------------------
# CDRs (Charge Detail Records) — ver docs/object_ocpi_cdr.md
# ---------------------------------------------------------------------------


class GeoLocation(BaseModel):
    model_config = ConfigDict(extra="allow")

    latitude: str
    longitude: str


class CdrToken(BaseModel):
    model_config = ConfigDict(extra="allow")

    country_code: str
    party_id: str
    uid: str
    type: str
    contract_id: str


class CdrLocation(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    coordinates: GeoLocation | None = None
    evse_id: str | None = None
    evse_uid: str | None = None
    connector_id: str | None = None
    connector_standard: str | None = None
    connector_format: str | None = None
    connector_power_type: str | None = None


class ChargingPeriodDimension(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    volume: float


class ChargingPeriod(BaseModel):
    model_config = ConfigDict(extra="allow")

    start_date_time: datetime
    dimensions: list[ChargingPeriodDimension]


class Price(BaseModel):
    model_config = ConfigDict(extra="allow")

    excl_vat: float
    incl_vat: float


class Cdr(BaseModel):
    """Módulo CDRs — Charge Detail Record completo, emitido por el CPO."""

    model_config = ConfigDict(extra="allow")

    country_code: str
    party_id: str
    id: str
    start_date_time: datetime
    end_date_time: datetime
    session_id: str | None = None
    cdr_token: CdrToken
    auth_method: str
    authorization_reference: str | None = None
    cdr_location: CdrLocation
    currency: str
    tariffs: list[Tariff] = []
    charging_periods: list[ChargingPeriod] = []
    total_cost: Price
    total_fixed_cost: Price | None = None
    total_energy: float
    total_energy_cost: Price | None = None
    total_time: float
    total_time_cost: Price | None = None
    last_updated: datetime


# ---------------------------------------------------------------------------
# Tokens & Authorisation
# ---------------------------------------------------------------------------


class TokenType(str, Enum):
    AD_HOC_USER = "AD_HOC_USER"
    APP_USER = "APP_USER"
    OTHER = "OTHER"
    RFID = "RFID"


class Token(BaseModel):
    """Módulo Tokens & Authorisation — identificadores de usuario."""

    model_config = ConfigDict(extra="allow")

    uid: str
    type: TokenType
    contract_id: str


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


class CommandTokenRef(BaseModel):
    model_config = ConfigDict(extra="allow")

    uid: str


class StartSessionCommand(BaseModel):
    """Módulo Commands — Start/Stop/Unlock remotos."""

    model_config = ConfigDict(extra="allow")

    token: CommandTokenRef
    location_id: str
    evse_uid: str | None = None


# ---------------------------------------------------------------------------
# Invoice Reconciliation (Edition 2)
# ---------------------------------------------------------------------------


class InvoiceReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    MISMATCHED = "MISMATCHED"
    PENDING = "PENDING"


class InvoiceReconciliation(BaseModel):
    """Módulo Invoice Reconciliation — consistencia entre CDRs y facturas."""

    model_config = ConfigDict(extra="allow")

    cdr_id: str
    invoice_reference: str
    status: InvoiceReconciliationStatus


# ---------------------------------------------------------------------------
# Charging Profiles (Smart Charging)
# ---------------------------------------------------------------------------


class ChargingProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    start_date_time: datetime
    charging_rate_unit: str
    limit: float


class ChargingProfileRequest(BaseModel):
    """Módulo Charging Profiles — límites de potencia / smart charging."""

    model_config = ConfigDict(extra="allow")

    charging_profile: ChargingProfile
