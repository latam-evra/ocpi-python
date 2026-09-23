"""Módulo Commands (mod_commands), implementado server-side en el Hub.

Field shapes mirror lib/ocpi/commands.ts y lib/ocpi/schemas/command.ts.

El módulo más asimétrico de los 5: no es CRUD. El SDK expone 5 métodos
tipados para enviar cada tipo de comando (uno por command_type) más
get_command(), cuyo GET vive en /commands/callback/{command_id} (no en
/commands/{command_type}) — ver client.py.

``response_url`` NO lo genera el SDK: a diferencia del Hub (que arma la
URL de callback interna hacia sí mismo), el llamador del SDK es un eMSP
externo real y debe pasar su propio response_url público; el SDK solo lo
forwardea tal cual en el body.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from .sessions import TokenType

__all__ = [
    "CommandTokenRef",
    "StartSessionCommand",
    "ReserveNowCommand",
    "StopSessionCommand",
    "UnlockConnectorCommand",
    "CancelReservationCommand",
    "CommandAckResult",
    "CommandAck",
    "CommandFinalResult",
    "CommandType",
    "Command",
]


class CommandTokenRef(BaseModel):
    """Subconjunto de CdrToken usado en comandos — sin country_code/party_id."""

    uid: str
    type: TokenType
    contract_id: str


class StartSessionCommand(BaseModel):
    response_url: str
    country_code: str
    party_id: str
    token: CommandTokenRef
    location_id: str
    evse_uid: str | None = None


class ReserveNowCommand(BaseModel):
    response_url: str
    country_code: str
    party_id: str
    token: CommandTokenRef
    expiry_date: str
    reservation_id: str
    location_id: str
    evse_uid: str | None = None


class StopSessionCommand(BaseModel):
    response_url: str
    country_code: str
    party_id: str
    session_id: str


class UnlockConnectorCommand(BaseModel):
    response_url: str
    country_code: str
    party_id: str
    session_id: str


class CancelReservationCommand(BaseModel):
    response_url: str
    country_code: str
    party_id: str
    session_id: str


class CommandAckResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    UNKNOWN_SESSION = "UNKNOWN_SESSION"


class CommandAck(BaseModel):
    result: CommandAckResult
    timeout: float
    message: dict | None = None


class CommandFinalResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    UNKNOWN_RESERVATION = "UNKNOWN_RESERVATION"


class CommandType(str, Enum):
    CANCEL_RESERVATION = "CANCEL_RESERVATION"
    RESERVE_NOW = "RESERVE_NOW"
    START_SESSION = "START_SESSION"
    STOP_SESSION = "STOP_SESSION"
    UNLOCK_CONNECTOR = "UNLOCK_CONNECTOR"


class Command(BaseModel):
    """Respuesta de GET /commands/callback/{command_id}."""

    id: str
    type: CommandType
    payload: object
    ack_result: CommandAckResult | None = None
    ack_message: dict | None = None
    final_result: CommandFinalResult | None = None
    final_result_received_at: str | None = None
    last_updated: str
