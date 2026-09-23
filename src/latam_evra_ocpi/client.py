"""Cliente async para el Hub de roaming OCPI 2.3.0 de LATAM EV Roaming Alliance."""

from __future__ import annotations

from typing import Any

import httpx

from .exceptions import OcpiError
from .models.cdrs import Cdr, CdrInput, CdrsPage
from .models.charging_profiles import (
    ChargingProfile,
    ChargingProfileAck,
    ChargingProfileRequestRecord,
    DeleteChargingProfileRequest,
    GetActiveChargingProfileRequest,
    SetChargingProfileRequest,
)
from .models.commands import (
    CancelReservationCommand,
    Command,
    CommandAck,
    ReserveNowCommand,
    StartSessionCommand,
    StopSessionCommand,
    UnlockConnectorCommand,
)
from .models.credentials import (
    Credentials,
    CredentialsRole,
    VersionDetails,
    VersionEntry,
)
from .models.envelope import OcpiResponse
from .models.hub_client_info import HubClientInfoEntry, HubClientInfoPage
from .models.invoice_reconciliation import (
    InvoiceReconciliation,
    InvoiceReconciliationInput,
    InvoiceReconciliationsPage,
)
from .models.locations import Location, LocationInput, LocationsPage
from .models.sessions import Session, SessionInput, SessionsPage
from .models.tariffs import Tariff, TariffInput, TariffsPage
from .models.tokens import AuthorizeResult, Token, TokenInput, TokensPage
from .status import OCPI_STATUS

DEFAULT_BASE_URL = "https://latam-evra.org/api/ocpi/2.3.0"


class OcpiClient:
    """Cliente OCPI 2.3.0 para el Hub LATAM EV Roaming Alliance (LEA).

    Ejemplo de uso (handshake de Credentials completo)::

        import asyncio
        from latam_evra_ocpi import OcpiClient

        async def main():
            async with OcpiClient(base_url="https://hub.example.com/api/ocpi/2.3.0") as client:
                versions = await client.get_versions()
                details = await client.get_details()

                credentials = await client.register_credentials(
                    token_a="TOKEN_A_RECIBIDO_DEL_ADMIN",
                    url="https://mi-csms.example.com/ocpi/versions",
                    roles=[{"role": "CPO", "party_id": "CHG", "country_code": "CL"}],
                )
                token_b = credentials.token  # guardar de forma segura

        asyncio.run(main())

    Todos los módulos del roadmap OCPI 2.3.0 del Hub están implementados:
    Credentials & Registration, Locations, Tariffs, Hub Client Info,
    Sessions, CDRs, Tokens & Authorisation, Commands, Charging Profiles e
    Invoice Reconciliation.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "OcpiClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _auth_header(token: str) -> dict[str, str]:
        return {"Authorization": f"Token {token}"}

    def _unwrap(self, response: httpx.Response) -> dict[str, Any]:
        """Parsea el sobre OCPI y lanza OcpiError si status_code indica error."""
        try:
            payload = response.json()
        except ValueError as exc:
            raise OcpiError(
                OCPI_STATUS.SERVER_ERROR,
                f"Respuesta no-JSON del Hub (HTTP {response.status_code}).",
                http_status=response.status_code,
            ) from exc

        status_code = payload.get("status_code")
        status_message = payload.get("status_message", "")

        if status_code != OCPI_STATUS.SUCCESS:
            raise OcpiError(
                status_code if status_code is not None else OCPI_STATUS.SERVER_ERROR,
                status_message or "El Hub devolvió un error sin mensaje.",
                http_status=response.status_code,
            )

        return payload

    # -- Credentials & Registration (implementado) --------------------------

    async def get_versions(self) -> list[VersionEntry]:
        """``GET /versions`` — versiones OCPI soportadas por el Hub."""
        response = await self._http.get(f"{self.base_url}/versions")
        payload = self._unwrap(response)
        envelope = OcpiResponse[list[VersionEntry]].model_validate(payload)
        return envelope.data

    async def get_details(self) -> VersionDetails:
        """``GET /details`` — endpoints del Hub para OCPI 2.3.0."""
        response = await self._http.get(f"{self.base_url}/details")
        payload = self._unwrap(response)
        envelope = OcpiResponse[VersionDetails].model_validate(payload)
        return envelope.data

    async def register_credentials(
        self,
        token_a: str,
        url: str,
        roles: list[CredentialsRole | dict[str, Any]],
    ) -> Credentials:
        """``POST /credentials`` — handshake inicial con ``TOKEN_A``.

        Devuelve las credenciales del Hub, incluyendo el ``TOKEN_B`` nuevo
        que debe guardarse de forma segura para futuras llamadas
        (``renew_credentials`` / ``terminate_credentials``).
        """
        body = {
            "token": token_a,
            "url": url,
            "roles": [
                role.model_dump() if isinstance(role, CredentialsRole) else role
                for role in roles
            ],
        }
        response = await self._http.post(
            f"{self.base_url}/credentials",
            json=body,
            headers=self._auth_header(token_a),
        )
        payload = self._unwrap(response)
        envelope = OcpiResponse[Credentials].model_validate(payload)
        return envelope.data

    async def renew_credentials(self, token_b: str) -> Credentials:
        """``PUT /credentials`` — renueva el ``TOKEN_B`` vigente."""
        response = await self._http.put(
            f"{self.base_url}/credentials",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        envelope = OcpiResponse[Credentials].model_validate(payload)
        return envelope.data

    async def terminate_credentials(self, token_b: str) -> None:
        """``DELETE /credentials`` — termina la conexión OCPI con el Hub."""
        response = await self._http.delete(
            f"{self.base_url}/credentials",
            headers=self._auth_header(token_b),
        )
        self._unwrap(response)

    # -- Locations (implementado) -------------------------------------------

    async def get_locations(
        self, token_b: str, offset: int = 0, limit: int = 50
    ) -> LocationsPage:
        """``GET /locations`` — listado paginado de locations publicadas."""
        response = await self._http.get(
            f"{self.base_url}/locations",
            params={"offset": offset, "limit": limit},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        locations = [Location.model_validate(item) for item in payload["data"]]
        return LocationsPage(locations=locations, total=len(locations))

    async def get_location(
        self, token_b: str, country_code: str, party_id: str, location_id: str
    ) -> Location:
        """``GET /locations/{country_code}/{party_id}/{location_id}``."""
        response = await self._http.get(
            f"{self.base_url}/locations/{country_code}/{party_id}/{location_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Location.model_validate(payload["data"])

    async def put_location(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        location_id: str,
        body: LocationInput,
    ) -> Location:
        """``PUT /locations/{country_code}/{party_id}/{location_id}``."""
        response = await self._http.put(
            f"{self.base_url}/locations/{country_code}/{party_id}/{location_id}",
            json=body.model_dump(exclude_none=True),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Location.model_validate(payload["data"])

    async def patch_location(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        location_id: str,
        body: dict,
    ) -> Location:
        """``PATCH /locations/{country_code}/{party_id}/{location_id}``."""
        response = await self._http.patch(
            f"{self.base_url}/locations/{country_code}/{party_id}/{location_id}",
            json=body,
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Location.model_validate(payload["data"])

    # -- Tariffs (implementado) ----------------------------------------------

    async def get_tariffs(
        self, token_b: str, offset: int = 0, limit: int = 50
    ) -> TariffsPage:
        """``GET /tariffs`` — listado paginado de tariffs publicados."""
        response = await self._http.get(
            f"{self.base_url}/tariffs",
            params={"offset": offset, "limit": limit},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        tariffs = [Tariff.model_validate(item) for item in payload["data"]]
        return TariffsPage(tariffs=tariffs, total=len(tariffs))

    async def get_tariff(
        self, token_b: str, country_code: str, party_id: str, tariff_id: str
    ) -> Tariff:
        """``GET /tariffs/{country_code}/{party_id}/{tariff_id}``."""
        response = await self._http.get(
            f"{self.base_url}/tariffs/{country_code}/{party_id}/{tariff_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Tariff.model_validate(payload["data"])

    async def put_tariff(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        tariff_id: str,
        body: TariffInput,
    ) -> Tariff:
        """``PUT /tariffs/{country_code}/{party_id}/{tariff_id}``."""
        response = await self._http.put(
            f"{self.base_url}/tariffs/{country_code}/{party_id}/{tariff_id}",
            json=body.model_dump(exclude_none=True),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Tariff.model_validate(payload["data"])

    async def delete_tariff(
        self, token_b: str, country_code: str, party_id: str, tariff_id: str
    ) -> None:
        """``DELETE /tariffs/{country_code}/{party_id}/{tariff_id}``."""
        response = await self._http.delete(
            f"{self.base_url}/tariffs/{country_code}/{party_id}/{tariff_id}",
            headers=self._auth_header(token_b),
        )
        self._unwrap(response)

    # -- Hub Client Info (implementado) --------------------------------------

    async def list_hub_client_info(
        self, token_b: str, offset: int = 0, limit: int = 50
    ) -> HubClientInfoPage:
        """``GET /hubclientinfo`` — listado paginado de clientes conocidos por el Hub."""
        response = await self._http.get(
            f"{self.base_url}/hubclientinfo",
            params={"offset": offset, "limit": limit},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        entries = [HubClientInfoEntry.model_validate(item) for item in payload["data"]]
        return HubClientInfoPage(entries=entries, total=len(entries))

    async def get_hub_client_info(
        self, token_b: str, country_code: str, party_id: str
    ) -> list[HubClientInfoEntry]:
        """``GET /hubclientinfo/{country_code}/{party_id}``."""
        response = await self._http.get(
            f"{self.base_url}/hubclientinfo/{country_code}/{party_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return [HubClientInfoEntry.model_validate(item) for item in payload["data"]]

    # -- Sessions (implementado) ---------------------------------------------

    async def get_sessions(
        self, token_b: str, offset: int = 0, limit: int = 50
    ) -> SessionsPage:
        """``GET /sessions`` — listado paginado de sesiones de carga."""
        response = await self._http.get(
            f"{self.base_url}/sessions",
            params={"offset": offset, "limit": limit},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        sessions = [Session.model_validate(item) for item in payload["data"]]
        return SessionsPage(sessions=sessions, total=len(sessions))

    async def get_session(
        self, token_b: str, country_code: str, party_id: str, session_id: str
    ) -> Session:
        """``GET /sessions/{country_code}/{party_id}/{session_id}``."""
        response = await self._http.get(
            f"{self.base_url}/sessions/{country_code}/{party_id}/{session_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Session.model_validate(payload["data"])

    async def put_session(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        session_id: str,
        body: SessionInput,
    ) -> Session:
        """``PUT /sessions/{country_code}/{party_id}/{session_id}`` — upsert."""
        response = await self._http.put(
            f"{self.base_url}/sessions/{country_code}/{party_id}/{session_id}",
            json=body.model_dump(exclude_none=True, mode="json"),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Session.model_validate(payload["data"])

    async def patch_session(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        session_id: str,
        body: dict,
    ) -> Session:
        """``PATCH /sessions/{country_code}/{party_id}/{session_id}`` — parcial."""
        response = await self._http.patch(
            f"{self.base_url}/sessions/{country_code}/{party_id}/{session_id}",
            json=body,
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Session.model_validate(payload["data"])

    # -- CDRs (implementado) — inmutables, sin PUT/PATCH/DELETE --------------

    async def get_cdrs(
        self, token_b: str, offset: int = 0, limit: int = 50
    ) -> CdrsPage:
        """``GET /cdrs`` — listado paginado de Charge Detail Records."""
        response = await self._http.get(
            f"{self.base_url}/cdrs",
            params={"offset": offset, "limit": limit},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        cdrs = [Cdr.model_validate(item) for item in payload["data"]]
        return CdrsPage(cdrs=cdrs, total=len(cdrs))

    async def get_cdr(
        self, token_b: str, country_code: str, party_id: str, cdr_id: str
    ) -> Cdr:
        """``GET /cdrs/{country_code}/{party_id}/{cdr_id}``."""
        response = await self._http.get(
            f"{self.base_url}/cdrs/{country_code}/{party_id}/{cdr_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Cdr.model_validate(payload["data"])

    async def post_cdr(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        cdr_id: str,
        body: CdrInput,
    ) -> Cdr:
        """``POST /cdrs/{country_code}/{party_id}/{cdr_id}`` — crea (inmutable,
        una segunda POST con el mismo id devuelve 409)."""
        response = await self._http.post(
            f"{self.base_url}/cdrs/{country_code}/{party_id}/{cdr_id}",
            json=body.model_dump(exclude_none=True, mode="json"),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Cdr.model_validate(payload["data"])

    # -- Tokens & Authorisation (implementado) --------------------------------

    async def get_tokens(
        self, token_b: str, offset: int = 0, limit: int = 50
    ) -> TokensPage:
        """``GET /tokens`` — listado paginado de tokens."""
        response = await self._http.get(
            f"{self.base_url}/tokens",
            params={"offset": offset, "limit": limit},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        tokens = [Token.model_validate(item) for item in payload["data"]]
        return TokensPage(tokens=tokens, total=len(tokens))

    async def get_token(
        self, token_b: str, country_code: str, party_id: str, uid: str
    ) -> Token:
        """``GET /tokens/{country_code}/{party_id}/{token_uid}``."""
        response = await self._http.get(
            f"{self.base_url}/tokens/{country_code}/{party_id}/{uid}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Token.model_validate(payload["data"])

    async def put_token(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        uid: str,
        body: TokenInput,
    ) -> Token:
        """``PUT /tokens/{country_code}/{party_id}/{token_uid}`` — upsert."""
        response = await self._http.put(
            f"{self.base_url}/tokens/{country_code}/{party_id}/{uid}",
            json=body.model_dump(exclude_none=True, mode="json"),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Token.model_validate(payload["data"])

    async def patch_token(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        uid: str,
        body: dict,
    ) -> Token:
        """``PATCH /tokens/{country_code}/{party_id}/{token_uid}`` — parcial."""
        response = await self._http.patch(
            f"{self.base_url}/tokens/{country_code}/{party_id}/{uid}",
            json=body,
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Token.model_validate(payload["data"])

    async def delete_token(
        self, token_b: str, country_code: str, party_id: str, uid: str
    ) -> None:
        """``DELETE /tokens/{country_code}/{party_id}/{token_uid}``."""
        response = await self._http.delete(
            f"{self.base_url}/tokens/{country_code}/{party_id}/{uid}",
            headers=self._auth_header(token_b),
        )
        self._unwrap(response)

    async def authorize_token(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        uid: str,
        location_references: dict | None = None,
    ) -> AuthorizeResult:
        """``POST /tokens/{country_code}/{party_id}/{token_uid}/authorize``.

        Endpoint especial, no forma parte del CRUD de tokens. Nunca propaga
        un error de negocio: el Hub siempre resuelve a ``{"allowed": "..."}"``,
        incluso ante fallos internos (token inexistente, eMSP desconectado,
        timeout de 6s) — esos casos resuelven a ``{"allowed": "BLOCKED"}"``,
        no una excepción.
        """
        response = await self._http.post(
            f"{self.base_url}/tokens/{country_code}/{party_id}/{uid}/authorize",
            json=location_references or {},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return AuthorizeResult.model_validate(payload["data"])

    # -- Commands (implementado) — no es CRUD: 5 métodos tipados para enviar
    # cada tipo de comando más get_command(), cuyo GET vive en
    # /commands/callback/{command_id} (no en /commands/{command_type}).
    # response_url no lo genera el SDK: el llamador (un eMSP externo) debe
    # pasar su propio callback público, se forwardea tal cual.
    # -------------------------------------------------------------------

    async def _send_command(
        self, token_b: str, command_type: str, body: Any
    ) -> CommandAck:
        response = await self._http.post(
            f"{self.base_url}/commands/{command_type}",
            json=body.model_dump(exclude_none=True, mode="json"),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return CommandAck.model_validate(payload["data"])

    async def start_session(
        self, token_b: str, body: StartSessionCommand
    ) -> CommandAck:
        """``POST /commands/START_SESSION``."""
        return await self._send_command(token_b, "START_SESSION", body)

    async def reserve_now(
        self, token_b: str, body: ReserveNowCommand
    ) -> CommandAck:
        """``POST /commands/RESERVE_NOW``."""
        return await self._send_command(token_b, "RESERVE_NOW", body)

    async def stop_session(
        self, token_b: str, body: StopSessionCommand
    ) -> CommandAck:
        """``POST /commands/STOP_SESSION``."""
        return await self._send_command(token_b, "STOP_SESSION", body)

    async def unlock_connector(
        self, token_b: str, body: UnlockConnectorCommand
    ) -> CommandAck:
        """``POST /commands/UNLOCK_CONNECTOR``."""
        return await self._send_command(token_b, "UNLOCK_CONNECTOR", body)

    async def cancel_reservation(
        self, token_b: str, body: CancelReservationCommand
    ) -> CommandAck:
        """``POST /commands/CANCEL_RESERVATION``."""
        return await self._send_command(token_b, "CANCEL_RESERVATION", body)

    async def get_command(self, token_b: str, command_id: str) -> Command:
        """``GET /commands/callback/{command_id}`` — estado actual del comando.
        Si pasaron más de 30s sin respuesta, el propio GET marca ``TIMEOUT``
        automáticamente antes de devolver."""
        response = await self._http.get(
            f"{self.base_url}/commands/callback/{command_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return Command.model_validate(payload["data"])

    # -- Invoice Reconciliation (implementado) — solo PUT (upsert), sin POST,
    # a diferencia de CDRs que es POST-only.
    # -------------------------------------------------------------------

    async def get_invoice_reconciliations(
        self, token_b: str, offset: int = 0, limit: int = 50
    ) -> InvoiceReconciliationsPage:
        """``GET /invoicereconciliations`` — listado paginado."""
        response = await self._http.get(
            f"{self.base_url}/invoicereconciliations",
            params={"offset": offset, "limit": limit},
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        reconciliations = [
            InvoiceReconciliation.model_validate(item) for item in payload["data"]
        ]
        return InvoiceReconciliationsPage(
            reconciliations=reconciliations, total=len(reconciliations)
        )

    async def get_invoice_reconciliation(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        reconciliation_id: str,
    ) -> InvoiceReconciliation:
        """``GET /invoicereconciliations/{country_code}/{party_id}/{reconciliation_id}``."""
        response = await self._http.get(
            f"{self.base_url}/invoicereconciliations/{country_code}/{party_id}/{reconciliation_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return InvoiceReconciliation.model_validate(payload["data"])

    async def put_invoice_reconciliation(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        reconciliation_id: str,
        body: InvoiceReconciliationInput,
    ) -> InvoiceReconciliation:
        """``PUT /invoicereconciliations/{country_code}/{party_id}/{reconciliation_id}``
        — upsert. Si el body incluye ``discrepancy_amount``, el Hub calcula
        la conversión FX server-side y la respuesta trae
        ``discrepancy_currency``/``discrepancy_amount_usd``/``exchange_rate_used``;
        si no, esos 3 campos vienen ausentes."""
        response = await self._http.put(
            f"{self.base_url}/invoicereconciliations/{country_code}/{party_id}/{reconciliation_id}",
            json=body.model_dump(exclude_none=True, mode="json"),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return InvoiceReconciliation.model_validate(payload["data"])

    async def delete_invoice_reconciliation(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        reconciliation_id: str,
    ) -> None:
        """``DELETE /invoicereconciliations/{country_code}/{party_id}/{reconciliation_id}``."""
        response = await self._http.delete(
            f"{self.base_url}/invoicereconciliations/{country_code}/{party_id}/{reconciliation_id}",
            headers=self._auth_header(token_b),
        )
        self._unwrap(response)

    # -- Charging Profiles (implementado) — no es CRUD simétrico: un método
    # por acción sobre una sesión existente, más get_charging_profile(),
    # cuyo GET vive en /chargingprofiles/callback/{id} (no en
    # /chargingprofiles/{session_id}). response_url no lo genera el SDK: el
    # llamador (un eMSP externo) debe pasar su propio callback público, se
    # forwardea tal cual.
    # -------------------------------------------------------------------

    async def _request_charging_profile(
        self,
        token_b: str,
        action: str,
        country_code: str,
        party_id: str,
        session_id: str,
        body: Any,
    ) -> ChargingProfileAck:
        response = await self._http.post(
            f"{self.base_url}/chargingprofiles/{country_code}/{party_id}/{session_id}/{action}",
            json=body.model_dump(exclude_none=True, mode="json"),
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return ChargingProfileAck.model_validate(payload["data"])

    async def get_active_charging_profile(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        session_id: str,
        response_url: str,
    ) -> ChargingProfileAck:
        """``POST /chargingprofiles/{cc}/{pid}/{sid}/GET_ACTIVE_CHARGING_PROFILE``."""
        return await self._request_charging_profile(
            token_b,
            "GET_ACTIVE_CHARGING_PROFILE",
            country_code,
            party_id,
            session_id,
            GetActiveChargingProfileRequest(response_url=response_url),
        )

    async def set_charging_profile(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        session_id: str,
        response_url: str,
        charging_profile: ChargingProfile,
    ) -> ChargingProfileAck:
        """``POST /chargingprofiles/{cc}/{pid}/{sid}/PUT_CHARGING_PROFILE``."""
        return await self._request_charging_profile(
            token_b,
            "PUT_CHARGING_PROFILE",
            country_code,
            party_id,
            session_id,
            SetChargingProfileRequest(
                response_url=response_url, charging_profile=charging_profile
            ),
        )

    async def delete_charging_profile(
        self,
        token_b: str,
        country_code: str,
        party_id: str,
        session_id: str,
        response_url: str,
    ) -> ChargingProfileAck:
        """``POST /chargingprofiles/{cc}/{pid}/{sid}/DELETE_CHARGING_PROFILE``."""
        return await self._request_charging_profile(
            token_b,
            "DELETE_CHARGING_PROFILE",
            country_code,
            party_id,
            session_id,
            DeleteChargingProfileRequest(response_url=response_url),
        )

    async def get_charging_profile(
        self, token_b: str, charging_profile_id: str
    ) -> ChargingProfileRequestRecord:
        """``GET /chargingprofiles/callback/{id}`` — estado actual de la
        solicitud. Si pasaron más de 30s sin respuesta, el propio GET marca
        ``FAILED`` automáticamente antes de devolver."""
        response = await self._http.get(
            f"{self.base_url}/chargingprofiles/callback/{charging_profile_id}",
            headers=self._auth_header(token_b),
        )
        payload = self._unwrap(response)
        return ChargingProfileRequestRecord.model_validate(payload["data"])
