import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.models.charging_profiles import ChargingProfile
from latam_evra_ocpi.models.sessions import SessionInput

HUB_URL = os.environ.get("OCPI_HUB_TEST_URL", "http://localhost:3947")
REPO_ROOT = Path(__file__).resolve().parents[4]


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
        self.last_method: str | None = None


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
                                    "identifier": "chargingprofiles",
                                    "role": "CPO",
                                    "url": f"{state.base_url}/cpo/chargingprofiles",
                                }
                            ],
                        },
                        "status_code": 1000,
                    }
                )
                return
            if self.path.startswith("/cpo/chargingprofiles/"):
                state.last_method = "GET"
                self._send_json({"data": {"result": "ACCEPTED", "timeout": 30}, "status_code": 1000})
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):  # noqa: N802 - stdlib handler naming
            self._handle_write("POST")

        def do_PUT(self):  # noqa: N802 - stdlib handler naming
            self._handle_write("PUT")

        def do_DELETE(self):  # noqa: N802 - stdlib handler naming
            self._handle_write("DELETE")

        def _handle_write(self, method: str) -> None:
            if self.path.startswith("/cpo/chargingprofiles/"):
                length = int(self.headers.get("Content-Length", 0))
                if length:
                    self.rfile.read(length)
                state.last_method = method
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
async def test_charging_profiles_all_actions_against_real_hub(mock_cpo_server):
    cpo = create_test_registration("CPO", "CL", "CQ2")
    emsp = create_test_registration("EMSP", "AR", "EQ2")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            cpo_credentials = await client.register_credentials(
                token_a=cpo["rawTokenA"],
                url=f"{mock_cpo_server.base_url}/cpo/versions",
                roles=[{"role": "CPO", "party_id": "CQ2", "country_code": "CL"}],
            )
            cpo_token_b = cpo_credentials.token

            await client.put_session(
                cpo_token_b,
                "CL",
                "CQ2",
                "SES-CP-PY-1",
                SessionInput(
                    id="SES-CP-PY-1",
                    start_date_time="2026-09-23T09:00:00Z",
                    kwh=0,
                    cdr_token={
                        "country_code": "AR",
                        "party_id": "EQ2",
                        "uid": "TOK-CP-PY-1",
                        "type": "RFID",
                        "contract_id": "C-CP-PY-1",
                    },
                    auth_method="AUTH_REQUEST",
                    location_id="LOC-CP-PY-1",
                    evse_uid="EVSE-1",
                    connector_id="1",
                    currency="USD",
                    status="ACTIVE",
                ),
            )

            emsp_credentials = await client.register_credentials(
                token_a=emsp["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "EMSP", "party_id": "EQ2", "country_code": "AR"}],
            )
            emsp_token_b = emsp_credentials.token

            set_ack = await client.set_charging_profile(
                emsp_token_b,
                "CL",
                "CQ2",
                "SES-CP-PY-1",
                "https://emsp.example.com/callback",
                ChargingProfile(
                    charging_rate_unit="W",
                    charging_profile_period=[{"start_period": 0, "limit": 7400}],
                ),
            )
            assert set_ack.result == "ACCEPTED"
            assert mock_cpo_server.last_method == "PUT"

            get_ack = await client.get_active_charging_profile(
                emsp_token_b, "CL", "CQ2", "SES-CP-PY-1", "https://emsp.example.com/callback"
            )
            assert get_ack.result == "ACCEPTED"
            assert mock_cpo_server.last_method == "GET"

            delete_ack = await client.delete_charging_profile(
                emsp_token_b, "CL", "CQ2", "SES-CP-PY-1", "https://emsp.example.com/callback"
            )
            assert delete_ack.result == "ACCEPTED"
            assert mock_cpo_server.last_method == "DELETE"
    finally:
        cleanup_registration(cpo["registrationId"])
        cleanup_registration(emsp["registrationId"])
