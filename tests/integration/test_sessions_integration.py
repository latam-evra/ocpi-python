import json
import os
import subprocess
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sessions_put_get_patch_list_against_real_hub():
    registration = create_test_registration("CPO", "CL", "SP1")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            credentials = await client.register_credentials(
                token_a=registration["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "CPO", "party_id": "SP1", "country_code": "CL"}],
            )
            token_b = credentials.token

            created = await client.put_session(
                token_b,
                "CL",
                "SP1",
                "SES-PY-1",
                SessionInput(
                    id="SES-PY-1",
                    start_date_time="2026-09-23T09:00:00Z",
                    kwh=5.5,
                    cdr_token={
                        "country_code": "AR",
                        "party_id": "EVP",
                        "uid": "TOK-PY-1",
                        "type": "RFID",
                        "contract_id": "C-PY-1",
                    },
                    auth_method="WHITELIST",
                    location_id="LOC-PY-1",
                    evse_uid="EVSE-1",
                    connector_id="1",
                    currency="USD",
                    status="ACTIVE",
                ),
            )
            assert created.id == "SES-PY-1"
            assert created.country_code == "CL"
            assert created.status == "ACTIVE"

            fetched = await client.get_session(token_b, "CL", "SP1", "SES-PY-1")
            assert fetched.kwh == 5.5

            patched = await client.patch_session(
                token_b, "CL", "SP1", "SES-PY-1", {"kwh": 9.2, "status": "COMPLETED"}
            )
            assert patched.kwh == 9.2
            assert patched.status == "COMPLETED"

            page = await client.get_sessions(token_b, offset=0, limit=100)
            assert any(s.id == "SES-PY-1" for s in page.sessions)

            with pytest.raises(Exception):
                await client.patch_session(
                    token_b, "CL", "SP1", "DOES-NOT-EXIST", {"kwh": 1}
                )
    finally:
        cleanup_registration(registration["registrationId"])
