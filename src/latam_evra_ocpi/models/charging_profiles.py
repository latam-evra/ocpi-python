"""Módulo Charging Profiles (mod_charging_profiles), implementado
server-side en el Hub.

Field shapes mirror lib/ocpi/chargingProfiles.ts y
lib/ocpi/schemas/chargingProfile.ts.

Al igual que Commands, no es CRUD simétrico: el eMSP pide una acción
(GET_ACTIVE_CHARGING_PROFILE / PUT_CHARGING_PROFILE /
DELETE_CHARGING_PROFILE) sobre una sesión existente, el Hub la reenvía al
CPO y responde con un ACK inmediato; el resultado final llega async por
callback y se consulta con get_charging_profile(), cuyo GET vive en
/chargingprofiles/callback/{id} (no en /chargingprofiles/{session_id}) —
ver client.py.

``response_url`` NO lo genera el SDK: el llamador debe pasar su propio
callback público, se forwardea tal cual en el body.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

__all__ = [
    "ChargingProfilePeriod",
    "ChargingProfile",
    "GetActiveChargingProfileRequest",
    "SetChargingProfileRequest",
    "DeleteChargingProfileRequest",
    "ChargingProfileAckResult",
    "ChargingProfileAck",
    "ChargingProfileFinalResult",
    "ChargingProfileAction",
    "ChargingProfileRequestRecord",
]


class ChargingProfilePeriod(BaseModel):
    start_period: int
    limit: float


class ChargingProfile(BaseModel):
    start_date_time: str | None = None
    duration: int | None = None
    charging_rate_unit: str
    min_charging_rate: float | None = None
    charging_profile_period: list[ChargingProfilePeriod]


class GetActiveChargingProfileRequest(BaseModel):
    response_url: str


class SetChargingProfileRequest(BaseModel):
    response_url: str
    charging_profile: ChargingProfile


class DeleteChargingProfileRequest(BaseModel):
    response_url: str


class ChargingProfileAckResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    UNKNOWN_SESSION = "UNKNOWN_SESSION"


class ChargingProfileAck(BaseModel):
    result: ChargingProfileAckResult
    timeout: float


class ChargingProfileFinalResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    UNKNOWN_SESSION = "UNKNOWN_SESSION"


class ChargingProfileAction(str, Enum):
    GET_ACTIVE_CHARGING_PROFILE = "GET_ACTIVE_CHARGING_PROFILE"
    PUT_CHARGING_PROFILE = "PUT_CHARGING_PROFILE"
    DELETE_CHARGING_PROFILE = "DELETE_CHARGING_PROFILE"


class ChargingProfileRequestRecord(BaseModel):
    """Respuesta de GET /chargingprofiles/callback/{id}."""

    id: str
    session_id: str
    action: ChargingProfileAction
    ack_result: ChargingProfileAckResult | None = None
    final_result: ChargingProfileFinalResult | None = None
    charging_profile: ChargingProfile | None = None
    final_result_received_at: str | None = None
    last_updated: str
