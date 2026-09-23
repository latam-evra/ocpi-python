import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.sessions import SessionInput

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"

SAMPLE_SESSION = {
    "country_code": "AR",
    "party_id": "EVP",
    "id": "SES-1",
    "start_date_time": "2026-09-23T10:00:00Z",
    "kwh": 12.5,
    "cdr_token": {
        "country_code": "AR",
        "party_id": "EVP",
        "uid": "TOK-1",
        "type": "RFID",
        "contract_id": "C-1",
    },
    "auth_method": "AUTH_REQUEST",
    "location_id": "LOC-1",
    "evse_uid": "EVSE-1",
    "connector_id": "1",
    "currency": "USD",
    "status": "ACTIVE",
    "last_updated": "2026-09-23T10:00:00Z",
}


def _envelope(data, status_code=1000, status_message="Success"):
    return {
        "data": data,
        "status_code": status_code,
        "status_message": status_message,
        "timestamp": "2026-09-23T10:00:00Z",
    }


@pytest.mark.asyncio
async def test_put_session_devuelve_la_sesion_creada(httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/sessions/AR/EVP/SES-1",
        json=_envelope(SAMPLE_SESSION),
        status_code=201,
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.put_session(
            "TOKEN_B_1",
            "AR",
            "EVP",
            "SES-1",
            SessionInput(
                id="SES-1",
                start_date_time="2026-09-23T10:00:00Z",
                kwh=12.5,
                cdr_token={
                    "country_code": "AR",
                    "party_id": "EVP",
                    "uid": "TOK-1",
                    "type": "RFID",
                    "contract_id": "C-1",
                },
                auth_method="AUTH_REQUEST",
                location_id="LOC-1",
                evse_uid="EVSE-1",
                connector_id="1",
                currency="USD",
                status="ACTIVE",
            ),
        )

    assert result.id == "SES-1"
    assert result.status == "ACTIVE"


@pytest.mark.asyncio
async def test_patch_session_hace_patch_parcial(httpx_mock):
    httpx_mock.add_response(
        method="PATCH",
        url=f"{BASE_URL}/sessions/AR/EVP/SES-1",
        json=_envelope({**SAMPLE_SESSION, "status": "COMPLETED"}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.patch_session(
            "TOKEN_B_1", "AR", "EVP", "SES-1", {"status": "COMPLETED"}
        )

    assert result.status == "COMPLETED"


@pytest.mark.asyncio
async def test_get_session_devuelve_una_sesion(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/sessions/AR/EVP/SES-1",
        json=_envelope(SAMPLE_SESSION),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.get_session("TOKEN_B_1", "AR", "EVP", "SES-1")

    assert result.id == "SES-1"


@pytest.mark.asyncio
async def test_get_sessions_lista_con_paginacion(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/sessions?offset=0&limit=10",
        json=_envelope([SAMPLE_SESSION]),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        page = await client.get_sessions("TOKEN_B_1", offset=0, limit=10)

    assert page.total == 1
    assert page.sessions[0].id == "SES-1"


@pytest.mark.asyncio
async def test_get_session_lanza_ocpi_error_en_404(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/sessions/AR/EVP/DOES-NOT-EXIST",
        status_code=404,
        json=_envelope({}, status_code=2001, status_message="Session no encontrada."),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.get_session("TOKEN_B_1", "AR", "EVP", "DOES-NOT-EXIST")
