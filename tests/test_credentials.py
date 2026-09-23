"""Tests del módulo Credentials & Registration contra mocks HTTP del Hub."""

import pytest

from latam_evra_ocpi import OcpiError
from latam_evra_ocpi.status import OCPI_STATUS

from .conftest import BASE_URL


def _envelope(data, status_code=1000, status_message="Success"):
    return {
        "data": data,
        "status_code": status_code,
        "status_message": status_message,
        "timestamp": "2026-09-22T15:06:00Z",
    }


@pytest.mark.asyncio
async def test_get_versions_success(client, httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE_URL}/versions",
        json=_envelope([{"version": "2.3.0", "url": f"{BASE_URL}/details"}]),
    )

    versions = await client.get_versions()

    assert len(versions) == 1
    assert versions[0].version == "2.3.0"
    assert versions[0].url == f"{BASE_URL}/details"


@pytest.mark.asyncio
async def test_get_details_success(client, httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE_URL}/details",
        json=_envelope(
            {
                "version": "2.3.0",
                "endpoints": [
                    {
                        "identifier": "credentials",
                        "role": "HUB",
                        "url": f"{BASE_URL}/credentials",
                    }
                ],
            }
        ),
    )

    details = await client.get_details()

    assert details.version == "2.3.0"
    assert details.endpoints[0].identifier == "credentials"


@pytest.mark.asyncio
async def test_register_credentials_success(client, httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/credentials",
        json=_envelope(
            {
                "token": "TOKEN_B_abcdef123456",
                "url": f"{BASE_URL}/versions",
                "roles": [{"role": "HUB", "party_id": "LEA", "country_code": "ZZ"}],
            }
        ),
    )

    credentials = await client.register_credentials(
        token_a="TOKEN_A_seed",
        url="https://mi-csms.example.com/ocpi/versions",
        roles=[{"role": "CPO", "party_id": "CHG", "country_code": "CL"}],
    )

    assert credentials.token == "TOKEN_B_abcdef123456"
    assert credentials.roles[0].role == "HUB"

    sent_request = httpx_mock.get_requests()[0]
    assert sent_request.headers["authorization"] == "Token TOKEN_A_seed"


@pytest.mark.asyncio
async def test_register_credentials_unknown_token_raises_ocpi_error(client, httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/credentials",
        status_code=401,
        json=_envelope({}, status_code=OCPI_STATUS.UNKNOWN_TOKEN, status_message="TOKEN_A inválido."),
    )

    with pytest.raises(OcpiError) as exc_info:
        await client.register_credentials(
            token_a="TOKEN_A_invalido",
            url="https://mi-csms.example.com/ocpi/versions",
            roles=[{"role": "CPO", "party_id": "CHG", "country_code": "CL"}],
        )

    assert exc_info.value.status_code == OCPI_STATUS.UNKNOWN_TOKEN
    assert exc_info.value.status_message == "TOKEN_A inválido."
    assert exc_info.value.http_status == 401


@pytest.mark.asyncio
async def test_renew_credentials_success(client, httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/credentials",
        json=_envelope(
            {
                "token": "TOKEN_B_renewed",
                "url": f"{BASE_URL}/versions",
                "roles": [{"role": "HUB", "party_id": "LEA", "country_code": "ZZ"}],
            }
        ),
    )

    credentials = await client.renew_credentials(token_b="TOKEN_B_old")

    assert credentials.token == "TOKEN_B_renewed"
    sent_request = httpx_mock.get_requests()[0]
    assert sent_request.headers["authorization"] == "Token TOKEN_B_old"


@pytest.mark.asyncio
async def test_renew_credentials_unknown_token_raises(client, httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/credentials",
        status_code=401,
        json=_envelope({}, status_code=OCPI_STATUS.UNKNOWN_TOKEN, status_message="TOKEN_B inválido o conexión no activa."),
    )

    with pytest.raises(OcpiError) as exc_info:
        await client.renew_credentials(token_b="TOKEN_B_revoked")

    assert exc_info.value.status_code == OCPI_STATUS.UNKNOWN_TOKEN


@pytest.mark.asyncio
async def test_terminate_credentials_success(client, httpx_mock):
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE_URL}/credentials",
        json=_envelope({}),
    )

    await client.terminate_credentials(token_b="TOKEN_B_active")

    sent_request = httpx_mock.get_requests()[0]
    assert sent_request.headers["authorization"] == "Token TOKEN_B_active"


@pytest.mark.asyncio
async def test_terminate_credentials_unknown_token_raises(client, httpx_mock):
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE_URL}/credentials",
        status_code=401,
        json=_envelope({}, status_code=OCPI_STATUS.UNKNOWN_TOKEN, status_message="TOKEN_B inválido."),
    )

    with pytest.raises(OcpiError) as exc_info:
        await client.terminate_credentials(token_b="TOKEN_B_bogus")

    assert exc_info.value.status_code == OCPI_STATUS.UNKNOWN_TOKEN
