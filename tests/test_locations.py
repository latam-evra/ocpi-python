import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.locations import LocationInput

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"


@pytest.mark.asyncio
async def test_put_location_devuelve_la_location_creada(httpx_mock):
    location_payload = {
        "country_code": "CL",
        "party_id": "TST",
        "id": "LOC-1",
        "publish": True,
        "address": "x",
        "city": "x",
        "country": "CHL",
        "coordinates": {"latitude": "0", "longitude": "0"},
        "evses": [],
    }
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/locations/CL/TST/LOC-1",
        json={
            "data": location_payload,
            "status_code": 1000,
            "status_message": "Success",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.put_location(
            "TOKEN_B_1",
            "CL",
            "TST",
            "LOC-1",
            LocationInput(
                id="LOC-1",
                publish=True,
                address="x",
                city="x",
                country="CHL",
                coordinates={"latitude": "0", "longitude": "0"},
            ),
        )

    assert result.id == "LOC-1"


@pytest.mark.asyncio
async def test_get_locations_hace_get_con_paginacion(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/locations?offset=0&limit=10",
        json={
            "data": [
                {
                    "country_code": "CL",
                    "party_id": "TST",
                    "id": "LOC-1",
                    "publish": True,
                    "address": "x",
                    "city": "x",
                    "country": "CHL",
                    "coordinates": {"latitude": "0", "longitude": "0"},
                    "evses": [],
                },
            ],
            "status_code": 1000,
            "status_message": "Success",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        page = await client.get_locations("TOKEN_B_1", offset=0, limit=10)

    assert len(page.locations) == 1


@pytest.mark.asyncio
async def test_get_location_lanza_ocpi_error_en_404(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/locations/CL/TST/DOES-NOT-EXIST",
        status_code=404,
        json={
            "data": {},
            "status_code": 2001,
            "status_message": "Location no encontrada.",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.get_location("TOKEN_B_1", "CL", "TST", "DOES-NOT-EXIST")
