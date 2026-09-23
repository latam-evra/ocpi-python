import json
import os
import subprocess
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.models.tokens import TokenInput

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
async def test_tokens_put_get_patch_list_delete_and_authorize_against_real_hub():
    emsp = create_test_registration("EMSP", "AR", "TP1")
    cpo = create_test_registration("CPO", "CL", "TP2")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            emsp_credentials = await client.register_credentials(
                token_a=emsp["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "EMSP", "party_id": "TP1", "country_code": "AR"}],
            )
            emsp_token_b = emsp_credentials.token

            cpo_credentials = await client.register_credentials(
                token_a=cpo["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "CPO", "party_id": "TP2", "country_code": "CL"}],
            )
            cpo_token_b = cpo_credentials.token

            created = await client.put_token(
                emsp_token_b,
                "AR",
                "TP1",
                "TOK-PY-1",
                TokenInput(
                    uid="TOK-PY-1",
                    type="RFID",
                    contract_id="C-PY-1",
                    issuer="LATAM EVP",
                    valid=True,
                    whitelist="ALWAYS",
                ),
            )
            assert created.uid == "TOK-PY-1"
            assert created.country_code == "AR"

            fetched = await client.get_token(emsp_token_b, "AR", "TP1", "TOK-PY-1")
            assert fetched.issuer == "LATAM EVP"

            patched = await client.patch_token(
                emsp_token_b, "AR", "TP1", "TOK-PY-1", {"valid": False}
            )
            assert patched.valid is False

            page = await client.get_tokens(emsp_token_b, offset=0, limit=100)
            assert any(t.uid == "TOK-PY-1" for t in page.tokens)

            await client.delete_token(emsp_token_b, "AR", "TP1", "TOK-PY-1")
            with pytest.raises(Exception):
                await client.get_token(emsp_token_b, "AR", "TP1", "TOK-PY-1")

            # authorize_token nunca lanza error de negocio: token inexistente
            # resuelve a {"allowed": "BLOCKED"}, no una excepción.
            result = await client.authorize_token(
                cpo_token_b, "AR", "ZZZ", "DOES-NOT-EXIST-PY"
            )
            assert result.allowed == "BLOCKED"
    finally:
        cleanup_registration(emsp["registrationId"])
        cleanup_registration(cpo["registrationId"])
