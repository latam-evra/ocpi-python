"""Códigos de estado OCPI usados por el Hub.

Réplica de las constantes definidas en ``lib/ocpi/response.ts`` del Hub
(latam-evra.org), para que el cliente pueda interpretar el campo
``status_code`` del sobre OCPI sin tener que memorizar los valores numéricos.
"""

from __future__ import annotations

from typing import Final


class _OcpiStatus:
    """Namespace de solo lectura con los códigos de estado OCPI del Hub."""

    SUCCESS: Final[int] = 1000

    CLIENT_ERROR: Final[int] = 2000
    INVALID_PARAMETERS: Final[int] = 2001
    NOT_ENOUGH_INFO: Final[int] = 2002
    UNKNOWN_TOKEN: Final[int] = 2003

    SERVER_ERROR: Final[int] = 3000
    UNABLE_TO_USE_API: Final[int] = 3001
    UNSUPPORTED_VERSION: Final[int] = 3002


OCPI_STATUS = _OcpiStatus()

#: Cualquier status_code >= este valor (dentro de la convención OCPI 2000-3999)
#: representa un error del cliente o del servidor.
CLIENT_ERROR_RANGE_START: Final[int] = 2000
