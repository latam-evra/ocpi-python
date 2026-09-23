"""Cliente Python no oficial para el Hub de roaming OCPI 2.3.0 de LATAM EV Roaming Alliance (LEA).

Hoy el Hub solo implementa server-side el módulo ``Credentials & Registration``.
El resto de los módulos OCPI (Locations, Sessions, CDRs, Tariffs, Tokens,
Commands, Hub Client Info, Invoice Reconciliation, Charging Profiles) están
en el roadmap: sus modelos ya están tipados en este SDK, pero los métodos
correspondientes del cliente lanzan ``NotImplementedError`` hasta que el
backend del Hub los soporte.
"""

from .client import OcpiClient
from .exceptions import OcpiError
from .status import OCPI_STATUS

__all__ = [
    "OcpiClient",
    "OcpiError",
    "OCPI_STATUS",
]

__version__ = "0.1.0"
