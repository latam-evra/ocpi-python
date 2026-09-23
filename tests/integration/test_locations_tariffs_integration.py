import json
import os
import subprocess
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.models.locations import LocationInput
from latam_evra_ocpi.models.tariffs import TariffInput

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
async def test_locations_and_tariffs_against_real_hub():
    registration = create_test_registration("CPO", "CL", "PY2")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            credentials = await client.register_credentials(
                token_a=registration["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "CPO", "party_id": "PY2", "country_code": "CL"}],
            )
            token_b = credentials.token

            created = await client.put_location(
                token_b,
                "CL",
                "PY2",
                "LOC-PY-1",
                LocationInput(
                    id="LOC-PY-1",
                    publish=True,
                    address="Av. Python 456",
                    city="Santiago",
                    country="CHL",
                    coordinates={"latitude": "-33.4", "longitude": "-70.6"},
                ),
            )
            assert created.id == "LOC-PY-1"

            fetched = await client.get_location(token_b, "CL", "PY2", "LOC-PY-1")
            assert fetched.address == "Av. Python 456"

            patched = await client.patch_location(
                token_b, "CL", "PY2", "LOC-PY-1", {"city": "Valparaíso"}
            )
            assert patched.city == "Valparaíso"

            page = await client.get_locations(token_b, offset=0, limit=100)
            assert any(loc.id == "LOC-PY-1" for loc in page.locations)

            await client.put_tariff(
                token_b,
                "CL",
                "PY2",
                "TAR-PY-1",
                TariffInput(
                    id="TAR-PY-1",
                    currency="USD",
                    elements=[{"price_components": [{"type": "ENERGY", "price": 0.4, "step_size": 1}]}],
                ),
            )
            tariff = await client.get_tariff(token_b, "CL", "PY2", "TAR-PY-1")
            assert tariff.currency == "USD"

            await client.delete_tariff(token_b, "CL", "PY2", "TAR-PY-1")

            with pytest.raises(Exception):
                await client.get_tariff(token_b, "CL", "PY2", "TAR-PY-1")
    finally:
        cleanup_registration(registration["registrationId"])
