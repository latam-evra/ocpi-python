import json
import os
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.models.commands import (
    CancelReservationCommand,
    ReserveNowCommand,
    StartSessionCommand,
    StopSessionCommand,
    UnlockConnectorCommand,
)
from latam_evra_ocpi.models.locations import LocationInput
from latam_evra_ocpi.models.sessions import SessionInput

HUB_URL = os.environ.get("OCPI_HUB_TEST_URL", "http://localhost:3947")
REPO_ROOT = Path(__file__).resolve().parents[4]

CALLBACK_ID_RE = re.compile(r"/commands/callback/([^/]+)$")


def create_test_registration(role: str, country_code: str, party_id: str) -> dict:
    result = subprocess.run(
        [
            "npx",
            "tsx",
            "scripts/create-test-registration.ts",
            "--role",
            role,
            "--country-code",
            country_code,
            "--party-id",
            party_id,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip())


def cleanup_registration(registration_id: str) -> None:
    subprocess.run(
        ["npx", "tsx", "scripts/create-test-registration.ts", "--cleanup", registration_id],
        cwd=REPO_ROOT,
        check=True,
    )


class _MockCpoState:
    def __init__(self) -> None:
        self.base_url = ""
        self.last_command_id: str | None = None


def _make_handler(state: _MockCpoState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002 - silence test server logs
            pass

        def _send_json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802 - stdlib handler naming
            if self.path == "/cpo/versions":
                self._send_json(
                    {
                        "data": [{"version": "2.3.0", "url": f"{state.base_url}/cpo/details"}],
                        "status_code": 1000,
                    }
                )
                return
            if self.path == "/cpo/details":
                self._send_json(
                    {
                        "data": {
                            "version": "2.3.0",
                            "endpoints": [
                                {
                                    "identifier": "commands",
                                    "role": "CPO",
                                    "url": f"{state.base_url}/cpo/commands",
                                }
                            ],
                        },
                        "status_code": 1000,
                    }
                )
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):  # noqa: N802 - stdlib handler naming
            if self.path.startswith("/cpo/commands/"):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw) if raw else {}
                    response_url = body.get("response_url")
                    if response_url:
                        match = CALLBACK_ID_RE.search(response_url)
                        if match:
                            state.last_command_id = match.group(1)
                except (ValueError, TypeError):
                    pass
                self._send_json({"data": {"result": "ACCEPTED", "timeout": 30}, "status_code": 1000})
                return
            self.send_response(404)
            self.end_headers()

    return Handler


@pytest.fixture
def mock_cpo_server():
    state = _MockCpoState()
    handler_cls = _make_handler(state)
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    state.base_url = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_commands_all_types_plus_get_command_against_real_hub(mock_cpo_server):
    cpo = create_test_registration("CPO", "CL", "CM2")
    emsp = create_test_registration("EMSP", "AR", "EM2")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            cpo_credentials = await client.register_credentials(
                token_a=cpo["rawTokenA"],
                url=f"{mock_cpo_server.base_url}/cpo/versions",
                roles=[{"role": "CPO", "party_id": "CM2", "country_code": "CL"}],
            )
            cpo_token_b = cpo_credentials.token

            await client.put_location(
                cpo_token_b,
                "CL",
                "CM2",
                "LOC-CMD-PY-1",
                LocationInput(
                    id="LOC-CMD-PY-1",
                    publish=True,
                    address="x",
                    city="x",
                    country="CHL",
                    coordinates={"latitude": "0", "longitude": "0"},
                ),
            )
            await client.put_session(
                cpo_token_b,
                "CL",
                "CM2",
                "SES-CMD-PY-1",
                SessionInput(
                    id="SES-CMD-PY-1",
                    start_date_time="2026-09-23T09:00:00Z",
                    kwh=0,
                    cdr_token={
                        "country_code": "AR",
                        "party_id": "EM2",
                        "uid": "TOK-CMD-PY-1",
                        "type": "RFID",
                        "contract_id": "C-CMD-PY-1",
                    },
                    auth_method="AUTH_REQUEST",
                    location_id="LOC-CMD-PY-1",
                    evse_uid="EVSE-1",
                    connector_id="1",
                    currency="USD",
                    status="ACTIVE",
                ),
            )

            emsp_credentials = await client.register_credentials(
                token_a=emsp["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "EMSP", "party_id": "EM2", "country_code": "AR"}],
            )
            emsp_token_b = emsp_credentials.token

            start_ack = await client.start_session(
                emsp_token_b,
                StartSessionCommand(
                    response_url="https://emsp.example.com/callback",
                    country_code="CL",
                    party_id="CM2",
                    token={"uid": "TOK-CMD-PY-1", "type": "RFID", "contract_id": "C-CMD-PY-1"},
                    location_id="LOC-CMD-PY-1",
                ),
            )
            assert start_ack.result == "ACCEPTED"
            assert start_ack.timeout == 30

            stop_ack = await client.stop_session(
                emsp_token_b,
                StopSessionCommand(
                    response_url="https://emsp.example.com/callback",
                    country_code="CL",
                    party_id="CM2",
                    session_id="SES-CMD-PY-1",
                ),
            )
            assert stop_ack.result == "ACCEPTED"

            unlock_ack = await client.unlock_connector(
                emsp_token_b,
                UnlockConnectorCommand(
                    response_url="https://emsp.example.com/callback",
                    country_code="CL",
                    party_id="CM2",
                    session_id="SES-CMD-PY-1",
                ),
            )
            assert unlock_ack.result == "ACCEPTED"

            cancel_ack = await client.cancel_reservation(
                emsp_token_b,
                CancelReservationCommand(
                    response_url="https://emsp.example.com/callback",
                    country_code="CL",
                    party_id="CM2",
                    session_id="SES-CMD-PY-1",
                ),
            )
            assert cancel_ack.result == "ACCEPTED"

            reserve_ack = await client.reserve_now(
                emsp_token_b,
                ReserveNowCommand(
                    response_url="https://emsp.example.com/callback",
                    country_code="CL",
                    party_id="CM2",
                    token={"uid": "TOK-CMD-PY-1", "type": "RFID", "contract_id": "C-CMD-PY-1"},
                    expiry_date="2026-09-24T00:00:00Z",
                    reservation_id="RES-CMD-PY-1",
                    location_id="LOC-CMD-PY-1",
                ),
            )
            assert reserve_ack.result == "ACCEPTED"

            # El ACK que devuelve start_session() es el del CPO destino, no
            # trae el id del comando — el mock CPO lo captura leyendo el
            # response_url que el Hub reescribe internamente antes de
            # forwardear el POST.
            command_id = mock_cpo_server.last_command_id
            assert command_id is not None

            command = await client.get_command(emsp_token_b, command_id)
            assert command.id == command_id
            assert command.type == "RESERVE_NOW"
            assert command.ack_result == "ACCEPTED"
    finally:
        cleanup_registration(cpo["registrationId"])
        cleanup_registration(emsp["registrationId"])
