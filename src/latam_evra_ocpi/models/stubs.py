"""Modelos tipados para los módulos OCPI que están en el roadmap del Hub.

Charging Profiles es el único módulo que sigue sin implementación
server-side (ver ``docs/Roaming_hub_Latam.md`` y
``components/ModuleAccordion.tsx`` — única entrada "roadmap"). Sessions,
CDRs, Tokens & Authorisation, Commands e Invoice Reconciliation ya están
implementados por el Hub — sus modelos viven en sus propios archivos
(``models/sessions.py``, ``models/cdrs.py``, ``models/tokens.py``,
``models/commands.py``, ``models/invoice_reconciliation.py``).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

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
