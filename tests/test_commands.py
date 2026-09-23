import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.commands import (
    CancelReservationCommand,
    ReserveNowCommand,
    StartSessionCommand,
    StopSessionCommand,
    UnlockConnectorCommand,
)

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"


def _envelope(data, status_code=1000, status_message="Success"):
    return {
        "data": data,
        "status_code": status_code,
        "status_message": status_message,
        "timestamp": "2026-09-23T10:00:00Z",
    }


@pytest.mark.asyncio
async def test_start_session_hace_post_y_devuelve_el_ack(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/commands/START_SESSION",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.start_session(
            "TOKEN_B_1",
            StartSessionCommand(
                response_url="https://emsp.example.com/callback",
                country_code="CL",
                party_id="CM1",
                token={"uid": "TOK-1", "type": "RFID", "contract_id": "C-1"},
                location_id="LOC-1",
            ),
        )

    assert ack.result == "ACCEPTED"
    assert ack.timeout == 30


@pytest.mark.asyncio
async def test_reserve_now_hace_post_y_devuelve_el_ack(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/commands/RESERVE_NOW",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.reserve_now(
            "TOKEN_B_1",
            ReserveNowCommand(
                response_url="https://emsp.example.com/callback",
                country_code="CL",
                party_id="CM1",
                token={"uid": "TOK-1", "type": "RFID", "contract_id": "C-1"},
                expiry_date="2026-09-24T10:00:00Z",
                reservation_id="RES-1",
                location_id="LOC-1",
            ),
        )

    assert ack.result == "ACCEPTED"


@pytest.mark.asyncio
async def test_stop_session_hace_post_y_devuelve_el_ack(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/commands/STOP_SESSION",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.stop_session(
            "TOKEN_B_1",
            StopSessionCommand(
                response_url="https://emsp.example.com/callback",
                country_code="CL",
                party_id="CM1",
                session_id="SES-1",
            ),
        )

    assert ack.result == "ACCEPTED"


@pytest.mark.asyncio
async def test_unlock_connector_hace_post_y_devuelve_el_ack(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/commands/UNLOCK_CONNECTOR",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.unlock_connector(
            "TOKEN_B_1",
            UnlockConnectorCommand(
                response_url="https://emsp.example.com/callback",
                country_code="CL",
                party_id="CM1",
                session_id="SES-1",
            ),
        )

    assert ack.result == "ACCEPTED"


@pytest.mark.asyncio
async def test_cancel_reservation_hace_post_y_devuelve_el_ack(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/commands/CANCEL_RESERVATION",
        json=_envelope({"result": "ACCEPTED", "timeout": 30}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        ack = await client.cancel_reservation(
            "TOKEN_B_1",
            CancelReservationCommand(
                response_url="https://emsp.example.com/callback",
                country_code="CL",
                party_id="CM1",
                session_id="SES-1",
            ),
        )

    assert ack.result == "ACCEPTED"


@pytest.mark.asyncio
async def test_get_command_usa_la_ruta_callback(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/commands/callback/CMD-1",
        json=_envelope(
            {
                "id": "CMD-1",
                "type": "START_SESSION",
                "payload": {},
                "ack_result": "ACCEPTED",
                "final_result": "ACCEPTED",
                "last_updated": "2026-09-23T10:00:00Z",
            }
        ),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        command = await client.get_command("TOKEN_B_1", "CMD-1")

    assert command.id == "CMD-1"
    assert command.final_result == "ACCEPTED"


@pytest.mark.asyncio
async def test_start_session_lanza_ocpi_error_en_422(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/commands/START_SESSION",
        status_code=422,
        json=_envelope({}, status_code=2003, status_message="CPO destino desconectado."),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.start_session(
                "TOKEN_B_1",
                StartSessionCommand(
                    response_url="https://emsp.example.com/callback",
                    country_code="CL",
                    party_id="CM1",
                    token={"uid": "TOK-1", "type": "RFID", "contract_id": "C-1"},
                    location_id="LOC-1",
                ),
            )
