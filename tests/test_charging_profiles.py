import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.charging_profiles import ChargingProfile

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"


def _envelope(data, status_code=1000, status_message="Success"):
    return {
        "data": data,
        "status_code": status_code,
        "status_message": status_message,
        "timestamp": "2026-09-23T10:00:00Z",
    }


@pytest.mark.asyncio
async def test_set_charging_profile_hace_post_y_devuelve_el_ack(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/chargingprofiles/CL/CM1/SES-1/PUT_CHARGING_PROFILE",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.set_charging_profile(
            "TOKEN_B_1",
            "CL",
            "CM1",
            "SES-1",
            "https://emsp.example.com/callback",
            ChargingProfile(
                charging_rate_unit="W",
                charging_profile_period=[{"start_period": 0, "limit": 7400}],
            ),
        )

    assert ack.result == "ACCEPTED"
    assert ack.timeout == 30


@pytest.mark.asyncio
async def test_get_active_charging_profile_hace_post(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/chargingprofiles/CL/CM1/SES-1/GET_ACTIVE_CHARGING_PROFILE",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.get_active_charging_profile(
            "TOKEN_B_1", "CL", "CM1", "SES-1", "https://emsp.example.com/callback"
        )

    assert ack.result == "ACCEPTED"


@pytest.mark.asyncio
async def test_delete_charging_profile_hace_post(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/chargingprofiles/CL/CM1/SES-1/DELETE_CHARGING_PROFILE",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.delete_charging_profile(
            "TOKEN_B_1", "CL", "CM1", "SES-1", "https://emsp.example.com/callback"
        )

    assert ack.result == "ACCEPTED"


@pytest.mark.asyncio
async def test_get_charging_profile_usa_la_ruta_callback(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/chargingprofiles/callback/CP-1",
        json=_envelope(
            {
                "id": "CP-1",
                "session_id": "SES-1",
                "action": "PUT_CHARGING_PROFILE",
                "ack_result": "ACCEPTED",
                "final_result": "ACCEPTED",
                "last_updated": "2026-09-23T10:00:00Z",
            }
        ),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        record = await client.get_charging_profile("TOKEN_B_1", "CP-1")

    assert record.id == "CP-1"
    assert record.final_result == "ACCEPTED"


@pytest.mark.asyncio
async def test_set_charging_profile_lanza_ocpi_error_en_404(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/chargingprofiles/CL/CM1/SES-1/PUT_CHARGING_PROFILE",
        status_code=404,
        json=_envelope({}, status_code=2001, status_message="No se encontró la sesión referenciada."),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.set_charging_profile(
                "TOKEN_B_1",
                "CL",
                "CM1",
                "SES-1",
                "https://emsp.example.com/callback",
                ChargingProfile(
                    charging_rate_unit="W",
                    charging_profile_period=[{"start_period": 0, "limit": 7400}],
                ),
            )
