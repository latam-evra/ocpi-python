import json
import os
import subprocess
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.models.cdrs import CdrInput

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


def _cdr_input() -> CdrInput:
    return CdrInput(
        id="CDR-PY-1",
        start_date_time="2026-09-23T09:00:00Z",
        end_date_time="2026-09-23T10:00:00Z",
        cdr_token={
            "country_code": "AR",
            "party_id": "EVP",
            "uid": "TOK-PY-1",
            "type": "RFID",
            "contract_id": "C-PY-1",
        },
        auth_method="WHITELIST",
        cdr_location={
            "id": "LOC-PY-1",
            "address": "Av. Test 123",
            "city": "Santiago",
            "country": "CHL",
            "coordinates": {"latitude": "-33.4", "longitude": "-70.6"},
            "evse_uid": "EVSE-1",
            "connector_id": "1",
            "connector_standard": "IEC_62196_T2",
            "connector_format": "SOCKET",
            "connector_power_type": "AC_3_PHASE",
        },
        currency="USD",
        charging_periods=[
            {"start_date_time": "2026-09-23T09:00:00Z", "dimensions": [{"type": "ENERGY", "volume": 5.5}]}
        ],
        total_cost={"excl_vat": 2.5},
        total_energy=5.5,
        total_time=1,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cdrs_post_get_list_and_immutability_against_real_hub():
    registration = create_test_registration("CPO", "CL", "CP1")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            credentials = await client.register_credentials(
                token_a=registration["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "CPO", "party_id": "CP1", "country_code": "CL"}],
            )
            token_b = credentials.token

            created = await client.post_cdr(token_b, "CL", "CP1", "CDR-PY-1", _cdr_input())
            assert created.id == "CDR-PY-1"
            assert created.country_code == "CL"
            assert created.total_energy == 5.5

            fetched = await client.get_cdr(token_b, "CL", "CP1", "CDR-PY-1")
            assert fetched.currency == "USD"

            page = await client.get_cdrs(token_b, offset=0, limit=100)
            assert any(c.id == "CDR-PY-1" for c in page.cdrs)

            with pytest.raises(Exception):
                await client.post_cdr(token_b, "CL", "CP1", "CDR-PY-1", _cdr_input())
    finally:
        cleanup_registration(registration["registrationId"])
