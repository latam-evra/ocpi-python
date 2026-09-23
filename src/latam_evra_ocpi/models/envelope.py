"""El sobre de respuesta OCPI (``OcpiResponse``) usado por todos los endpoints del Hub."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class OcpiResponse(BaseModel, Generic[T]):
    """Sobre estándar OCPI: ``{ data, status_code, status_message, timestamp }``.

    Replica el formato devuelto por ``lib/ocpi/response.ts`` (funciones
    ``ocpiSuccess`` / ``ocpiError``) del Hub.
    """

    model_config = ConfigDict(extra="allow")

    data: T
    status_code: int
    status_message: str
    timestamp: datetime
