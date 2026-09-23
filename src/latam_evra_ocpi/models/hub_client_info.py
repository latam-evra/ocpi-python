from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class HubClientConnectionStatus(str, Enum):
    PLANNED = "PLANNED"
    CONNECTED = "CONNECTED"
    SUSPENDED = "SUSPENDED"
    STOPPED = "STOPPED"


class HubClientInfoEntry(BaseModel):
    """Módulo Hub Client Info — visibilidad de clientes (CPOs/eMSPs) conectados
    al Hub. Field shapes mirror lib/ocpi/hubClientInfo.ts (toEntry /
    STATUS_MAP) en el Hub."""

    party_id: str
    country_code: str
    role: str
    status: HubClientConnectionStatus
    last_updated: str


class HubClientInfoPage(BaseModel):
    entries: list[HubClientInfoEntry]
    total: int
