import json
import os
import subprocess
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient

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
async def test_hub_client_info_against_real_hub():
    registration = create_test_registration("CPO", "CL", "PY3")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            credentials = await client.register_credentials(
                token_a=registration["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "CPO", "party_id": "PY3", "country_code": "CL"}],
            )
            token_b = credentials.token

            page = await client.list_hub_client_info(token_b, offset=0, limit=100)
            own = next(
                (e for e in page.entries if e.party_id == "PY3" and e.country_code == "CL"),
                None,
            )
            assert own is not None
            assert own.role == "CPO"
            assert own.status == "CONNECTED"

            by_role = await client.get_hub_client_info(token_b, "CL", "PY3")
            assert len(by_role) == 1
            assert by_role[0].status == "CONNECTED"
    finally:
        cleanup_registration(registration["registrationId"])
