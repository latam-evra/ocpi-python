import json
import os
import subprocess
from pathlib import Path

import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.models.cdrs import CdrInput
from latam_evra_ocpi.models.invoice_reconciliation import InvoiceReconciliationInput

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
async def test_invoice_reconciliation_put_get_list_delete_and_fx_against_real_hub():
    registration = create_test_registration("CPO", "CL", "IP1")

    try:
        async with OcpiClient(base_url=f"{HUB_URL}/api/ocpi/2.3.0") as client:
            credentials = await client.register_credentials(
                token_a=registration["rawTokenA"],
                url=f"{HUB_URL}/api/ocpi/2.3.0/versions",
                roles=[{"role": "CPO", "party_id": "IP1", "country_code": "CL"}],
            )
            token_b = credentials.token

            # CDR en CLP (moneda soportada por Frankfurter vía BCCh) para el
            # caso con conversión FX real.
            await client.post_cdr(
                token_b,
                "CL",
                "IP1",
                "CDR-IP-1",
                CdrInput(
                    id="CDR-IP-1",
                    start_date_time="2026-09-23T09:00:00Z",
                    end_date_time="2026-09-23T10:00:00Z",
                    cdr_token={
                        "country_code": "AR",
                        "party_id": "EVP",
                        "uid": "TOK-IP-1",
                        "type": "RFID",
                        "contract_id": "C-IP-1",
                    },
                    auth_method="WHITELIST",
                    cdr_location={
                        "id": "LOC-IP-1",
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
                    currency="CLP",
                    charging_periods=[
                        {
                            "start_date_time": "2026-09-23T09:00:00Z",
                            "dimensions": [{"type": "ENERGY", "volume": 10}],
                        }
                    ],
                    total_cost={"excl_vat": 5000},
                    total_energy=10,
                    total_time=1,
                ),
            )

            created = await client.put_invoice_reconciliation(
                token_b,
                "CL",
                "IP1",
                "REC-PY-1",
                InvoiceReconciliationInput(
                    id="REC-PY-1", cdr_id="CDR-IP-1", status="PENDING"
                ),
            )
            assert created.id == "REC-PY-1"
            assert created.discrepancy_currency is None
            assert created.discrepancy_amount_usd is None
            assert created.exchange_rate_used is None

            fetched = await client.get_invoice_reconciliation(
                token_b, "CL", "IP1", "REC-PY-1"
            )
            assert fetched.status == "PENDING"

            page = await client.get_invoice_reconciliations(token_b, offset=0, limit=100)
            assert any(r.id == "REC-PY-1" for r in page.reconciliations)

            await client.delete_invoice_reconciliation(token_b, "CL", "IP1", "REC-PY-1")
            with pytest.raises(Exception):
                await client.get_invoice_reconciliation(token_b, "CL", "IP1", "REC-PY-1")

            # Caso con discrepancy_amount: conversión FX real (Frankfurter/BCCh).
            with_fx = await client.put_invoice_reconciliation(
                token_b,
                "CL",
                "IP1",
                "REC-PY-2",
                InvoiceReconciliationInput(
                    id="REC-PY-2",
                    cdr_id="CDR-IP-1",
                    status="DISPUTED",
                    discrepancy_description="Total cost mismatch",
                    discrepancy_amount={"excl_vat": 1000},
                ),
            )
            assert with_fx.discrepancy_currency == "CLP"
            assert with_fx.discrepancy_amount_usd is not None
            assert with_fx.discrepancy_amount_usd.excl_vat > 0
            assert with_fx.exchange_rate_used is not None
            assert with_fx.exchange_rate_used > 0

            await client.delete_invoice_reconciliation(token_b, "CL", "IP1", "REC-PY-2")

            # cdr_id que no resuelve: el PUT debe propagar OcpiError (400).
            with pytest.raises(Exception):
                await client.put_invoice_reconciliation(
                    token_b,
                    "CL",
                    "IP1",
                    "REC-PY-3",
                    InvoiceReconciliationInput(
                        id="REC-PY-3",
                        cdr_id="DOES-NOT-EXIST",
                        status="PENDING",
                        discrepancy_amount={"excl_vat": 10},
                    ),
                )
    finally:
        cleanup_registration(registration["registrationId"])
