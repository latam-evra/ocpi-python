"""Modelos del módulo Credentials & Registration (el único implementado hoy)."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    """Roles OCPI que puede declarar un participante al registrarse en el Hub."""

    CPO = "CPO"
    EMSP = "EMSP"
    HUB = "HUB"


class CredentialsRole(BaseModel):
    """Un rol OCPI dentro del body de ``credentials`` (POST/respuesta)."""

    model_config = ConfigDict(extra="allow")

    role: Role
    party_id: Annotated[str, Field(min_length=3, max_length=3)]
    country_code: Annotated[str, Field(min_length=2, max_length=2)]


class CredentialsRequest(BaseModel):
    """Body enviado en ``POST /api/ocpi/2.3.0/credentials``."""

    token: str
    url: str
    roles: list[CredentialsRole] = Field(min_length=1)


class Credentials(BaseModel):
    """``data`` de la respuesta de credentials (POST/PUT) del Hub."""

    model_config = ConfigDict(extra="allow")

    token: str
    url: str
    roles: list[CredentialsRole]


class VersionEntry(BaseModel):
    """Un elemento de ``GET /versions``."""

    model_config = ConfigDict(extra="allow")

    version: str
    url: str


class VersionEndpoint(BaseModel):
    """Un endpoint dentro de ``GET /details``."""

    model_config = ConfigDict(extra="allow")

    identifier: str
    role: str
    url: str


class VersionDetails(BaseModel):
    """``data`` de ``GET /api/ocpi/2.3.0/details``."""

    model_config = ConfigDict(extra="allow")

    version: str
    endpoints: list[VersionEndpoint]
