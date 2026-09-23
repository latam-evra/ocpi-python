import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"


@pytest.mark.asyncio
async def test_list_hub_client_info_hace_get_con_paginacion(httpx_mock):
    entry = {
        "party_id": "TST",
        "country_code": "CL",
        "role": "CPO",
        "status": "CONNECTED",
        "last_updated": "2026-01-01T00:00:00Z",
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/hubclientinfo?offset=0&limit=50",
        json={
            "data": [entry],
            "status_code": 1000,
            "status_message": "Success",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        page = await client.list_hub_client_info("TOKEN_B_1")

    assert page.total == 1
    assert page.entries[0].status == "CONNECTED"


@pytest.mark.asyncio
async def test_get_hub_client_info_hace_get_por_country_code_party_id(httpx_mock):
    entry = {
        "party_id": "TST",
        "country_code": "CL",
        "role": "EMSP",
        "status": "SUSPENDED",
        "last_updated": "2026-01-01T00:00:00Z",
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/hubclientinfo/CL/TST",
        json={
            "data": [entry],
            "status_code": 1000,
            "status_message": "Success",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        entries = await client.get_hub_client_info("TOKEN_B_1", "CL", "TST")

    assert len(entries) == 1
    assert entries[0].role == "EMSP"


@pytest.mark.asyncio
async def test_list_hub_client_info_lanza_ocpi_error_con_token_invalido(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/hubclientinfo?offset=0&limit=50",
        status_code=401,
        json={
            "data": {},
            "status_code": 2003,
            "status_message": "TOKEN_B inválido o conexión no activa.",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.list_hub_client_info("TOKEN_B_INVALID")
