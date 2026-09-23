"""Módulo Tokens & Authorisation (mod_tokens), implementado server-side en
el Hub.

Field shapes mirror lib/ocpi/tokens.ts (toPublicToken / tokenInputSchema).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from .sessions import TokenType

__all__ = [
    "TokenType",
    "TokenWhitelist",
    "TokenInput",
    "Token",
    "TokensPage",
    "AuthorizeResult",
]


class TokenWhitelist(str, Enum):
    NEVER = "NEVER"
    ALLOWED = "ALLOWED"
    ALLOWED_OFFLINE = "ALLOWED_OFFLINE"
    ALWAYS = "ALWAYS"


class TokenInput(BaseModel):
    uid: str
    type: TokenType
    contract_id: str
    visual_number: str | None = None
    issuer: str
    group_id: str | None = None
    valid: bool
    whitelist: TokenWhitelist
    language: str | None = None
    default_profile_type: str | None = None
    energy_contract: dict | None = None


class Token(TokenInput):
    country_code: str
    party_id: str
    last_updated: str


class TokensPage(BaseModel):
    tokens: list[Token]
    total: int


class AuthorizeResult(BaseModel):
    """Respuesta de ``POST .../authorize``. ``allowed`` refleja lo que
    devuelva el eMSP remoto (valores observados "ALLOWED"/"BLOCKED") — se
    trata como ``str``, no como enum cerrado."""

    allowed: str
