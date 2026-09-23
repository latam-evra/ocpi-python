"""Módulo Sessions (mod_sessions), implementado server-side en el Hub.

Field shapes mirror lib/ocpi/sessions.ts (toPublicSession /
sessionInputSchema).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    INVALID = "INVALID"
    PENDING = "PENDING"
    RESERVATION = "RESERVATION"


class TokenType(str, Enum):
    AD_HOC_USER = "AD_HOC_USER"
    APP_USER = "APP_USER"
    OTHER = "OTHER"
    RFID = "RFID"


class AuthMethod(str, Enum):
    AUTH_REQUEST = "AUTH_REQUEST"
    COMMAND = "COMMAND"
    WHITELIST = "WHITELIST"


class CdrToken(BaseModel):
    country_code: str
    party_id: str
    uid: str
    type: TokenType
    contract_id: str


class ChargingPeriodDimension(BaseModel):
    type: str
    volume: float


class ChargingPeriod(BaseModel):
    start_date_time: str
    dimensions: list[ChargingPeriodDimension]
    tariff_id: str | None = None


class CostAmount(BaseModel):
    excl_vat: float
    incl_vat: float | None = None


class SessionInput(BaseModel):
    id: str
    start_date_time: str
    end_date_time: str | None = None
    kwh: float
    cdr_token: CdrToken
    auth_method: AuthMethod
    authorization_reference: str | None = None
    location_id: str
    evse_uid: str
    connector_id: str
    meter_id: str | None = None
    currency: str
    charging_periods: list[ChargingPeriod] | None = None
    total_cost: CostAmount | None = None
    status: SessionStatus


class Session(SessionInput):
    country_code: str
    party_id: str
    last_updated: str


class SessionsPage(BaseModel):
    sessions: list[Session]
    total: int
