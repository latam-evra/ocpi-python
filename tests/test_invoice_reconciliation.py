import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.invoice_reconciliation import InvoiceReconciliationInput

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"

SAMPLE_RECORD_NO_FX = {
    "country_code": "CL",
    "party_id": "TST",
    "id": "REC-1",
    "cdr_id": "CDR-1",
    "status": "PENDING",
    "last_updated": "2026-09-23T10:00:00Z",
}

SAMPLE_RECORD_WITH_FX = {
    "country_code": "CL",
    "party_id": "TST",
    "id": "REC-2",
    "cdr_id": "CDR-2",
    "status": "DISPUTED",
    "discrepancy_amount": {"excl_vat": 1000},
    "discrepancy_currency": "CLP",
    "discrepancy_amount_usd": {"excl_vat": 1.05},
    "exchange_rate_used": 950.5,
    "last_updated": "2026-09-23T10:00:00Z",
}


def _envelope(data, status_code=1000, status_message="Success"):
    return {
        "data": data,
        "status_code": status_code,
        "status_message": status_message,
        "timestamp": "2026-09-23T10:00:00Z",
    }


@pytest.mark.asyncio
async def test_put_invoice_reconciliation_sin_discrepancy_amount_no_trae_campos_fx(httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/invoicereconciliations/CL/TST/REC-1",
        json=_envelope(SAMPLE_RECORD_NO_FX),
        status_code=201,
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.put_invoice_reconciliation(
            "TOKEN_B_1",
            "CL",
            "TST",
            "REC-1",
            InvoiceReconciliationInput(id="REC-1", cdr_id="CDR-1", status="PENDING"),
        )

    assert result.id == "REC-1"
    assert result.discrepancy_currency is None
    assert result.discrepancy_amount_usd is None
    assert result.exchange_rate_used is None


@pytest.mark.asyncio
async def test_put_invoice_reconciliation_con_discrepancy_amount_trae_campos_fx(httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/invoicereconciliations/CL/TST/REC-2",
        json=_envelope(SAMPLE_RECORD_WITH_FX),
        status_code=201,
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.put_invoice_reconciliation(
            "TOKEN_B_1",
            "CL",
            "TST",
            "REC-2",
            InvoiceReconciliationInput(
                id="REC-2",
                cdr_id="CDR-2",
                status="DISPUTED",
                discrepancy_amount={"excl_vat": 1000},
            ),
        )

    assert result.discrepancy_currency == "CLP"
    assert result.discrepancy_amount_usd.excl_vat == 1.05
    assert result.exchange_rate_used == 950.5


@pytest.mark.asyncio
async def test_get_invoice_reconciliation_devuelve_un_registro(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/invoicereconciliations/CL/TST/REC-1",
        json=_envelope(SAMPLE_RECORD_NO_FX),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.get_invoice_reconciliation("TOKEN_B_1", "CL", "TST", "REC-1")

    assert result.id == "REC-1"


@pytest.mark.asyncio
async def test_get_invoice_reconciliations_lista_con_paginacion(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/invoicereconciliations?offset=0&limit=10",
        json=_envelope([SAMPLE_RECORD_NO_FX]),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        page = await client.get_invoice_reconciliations("TOKEN_B_1", offset=0, limit=10)

    assert page.total == 1
    assert page.reconciliations[0].id == "REC-1"


@pytest.mark.asyncio
async def test_delete_invoice_reconciliation_no_lanza_en_exito(httpx_mock):
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE_URL}/invoicereconciliations/CL/TST/REC-1",
        json=_envelope({}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        await client.delete_invoice_reconciliation("TOKEN_B_1", "CL", "TST", "REC-1")


@pytest.mark.asyncio
async def test_put_invoice_reconciliation_lanza_ocpi_error_cuando_cdr_id_no_resuelve(httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/invoicereconciliations/CL/TST/REC-3",
        status_code=400,
        json=_envelope(
            {}, status_code=2001, status_message="CDR referenciado (CDR-X) no encontrado."
        ),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.put_invoice_reconciliation(
                "TOKEN_B_1",
                "CL",
                "TST",
                "REC-3",
                InvoiceReconciliationInput(
                    id="REC-3",
                    cdr_id="CDR-X",
                    status="PENDING",
                    discrepancy_amount={"excl_vat": 10},
                ),
            )
