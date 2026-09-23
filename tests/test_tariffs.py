import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.tariffs import TariffInput

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"


@pytest.mark.asyncio
async def test_put_tariff_devuelve_el_tariff_creado(httpx_mock):
    tariff_payload = {
        "country_code": "CL",
        "party_id": "TST",
        "id": "TAR-1",
        "currency": "USD",
        "elements": [{"price_components": [{"type": "ENERGY", "price": 0.35, "step_size": 1}]}],
    }
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/tariffs/CL/TST/TAR-1",
        json={
            "data": tariff_payload,
            "status_code": 1000,
            "status_message": "Success",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.put_tariff(
            "TOKEN_B_1",
            "CL",
            "TST",
            "TAR-1",
            TariffInput(
                id="TAR-1",
                currency="USD",
                elements=[{"price_components": [{"type": "ENERGY", "price": 0.35, "step_size": 1}]}],
            ),
        )

    assert result.id == "TAR-1"


@pytest.mark.asyncio
async def test_delete_tariff_no_lanza_en_exito(httpx_mock):
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE_URL}/tariffs/CL/TST/TAR-1",
        json={
            "data": {},
            "status_code": 1000,
            "status_message": "Success",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        await client.delete_tariff("TOKEN_B_1", "CL", "TST", "TAR-1")


@pytest.mark.asyncio
async def test_get_tariff_lanza_ocpi_error_en_404(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/tariffs/CL/TST/DOES-NOT-EXIST",
        status_code=404,
        json={
            "data": {},
            "status_code": 2001,
            "status_message": "Tariff no encontrado.",
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.get_tariff("TOKEN_B_1", "CL", "TST", "DOES-NOT-EXIST")
