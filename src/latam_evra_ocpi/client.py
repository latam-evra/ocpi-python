"""Cliente async para el Hub de roaming OCPI 2.3.0 de LATAM EV Roaming Alliance."""

from __future__ import annotations

from typing import Any

import httpx

from .exceptions import OcpiError, OcpiModuleNotAvailableError
from .models.credentials import (
    Credentials,
    CredentialsRole,
    VersionDetails,
    VersionEntry,
)
from .models.envelope import OcpiResponse
from .models.hub_client_info import HubClientInfoEntry, HubClientInfoPage
from .models.locations import Location, LocationInput, LocationsPage
from .models.tariffs import Tariff, TariffInput, TariffsPage
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

    Los módulos Credentials & Registration, Locations y Tariffs están
    implementados por el Hub. Los métodos de los demás módulos (Sessions,
    CDRs, Tokens, Commands, Hub Client Info, Invoice Reconciliation,
    Charging Profiles) lanzan ``NotImplementedError`` — ver README para el
    roadmap.
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

    # -- Módulos en roadmap (no implementados por el Hub todavía) -----------

    async def get_active_session(self, session_id: str) -> Any:
        """Módulo Sessions — ver ``latam_evra_ocpi.models.Session``."""
        raise OcpiModuleNotAvailableError("Sessions")

    async def get_cdrs(self, *_args: Any, **_kwargs: Any) -> Any:
        """Módulo CDRs — ver ``latam_evra_ocpi.models.Cdr``."""
        raise OcpiModuleNotAvailableError("CDRs")

    async def authorize_token(self, token_uid: str) -> Any:
        """Módulo Tokens & Authorisation — ver ``latam_evra_ocpi.models.Token``."""
        raise OcpiModuleNotAvailableError("Tokens & Authorisation")

    async def send_command(self, command: str, *_args: Any, **_kwargs: Any) -> Any:
        """Módulo Commands — ver ``latam_evra_ocpi.models.StartSessionCommand``."""
        raise OcpiModuleNotAvailableError("Commands")

    async def get_invoice_reconciliation(self, *_args: Any, **_kwargs: Any) -> Any:
        """Módulo Invoice Reconciliation — ver ``latam_evra_ocpi.models.InvoiceReconciliation``."""
        raise OcpiModuleNotAvailableError("Invoice Reconciliation")

    async def set_charging_profile(self, session_id: str, *_args: Any, **_kwargs: Any) -> Any:
        """Módulo Charging Profiles — ver ``latam_evra_ocpi.models.ChargingProfileRequest``."""
        raise OcpiModuleNotAvailableError("Charging Profiles")
