import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.cdrs import CdrInput

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"

SAMPLE_CDR = {
    "country_code": "CL",
    "party_id": "CHG",
    "id": "CDR-1",
    "start_date_time": "2026-09-22T14:15:00Z",
    "end_date_time": "2026-09-22T15:05:30Z",
    "cdr_token": {
        "country_code": "AR",
        "party_id": "EVP",
        "uid": "TOK-1",
        "type": "RFID",
        "contract_id": "C-1",
    },
    "auth_method": "AUTH_REQUEST",
    "cdr_location": {
        "id": "LOC-1",
        "address": "Av. x 1",
        "city": "Santiago",
        "country": "CHL",
        "coordinates": {"latitude": "-33.4", "longitude": "-70.6"},
        "evse_uid": "EVSE-1",
        "connector_id": "1",
        "connector_standard": "IEC_62196_T2_COMBO",
        "connector_format": "SOCKET",
        "connector_power_type": "DC",
    },
    "currency": "USD",
    "charging_periods": [
        {"start_date_time": "2026-09-22T14:15:00Z", "dimensions": [{"type": "ENERGY", "volume": 10.0}]}
    ],
    "total_cost": {"excl_vat": 5.0, "incl_vat": 5.95},
    "total_energy": 10.0,
    "total_time": 0.5,
    "last_updated": "2026-09-22T15:06:00Z",
}


def _envelope(data, status_code=1000, status_message="Success"):
    return {
        "data": data,
        "status_code": status_code,
        "status_message": status_message,
        "timestamp": "2026-09-22T15:06:00Z",
    }


def _cdr_input_kwargs():
    return dict(
        id="CDR-1",
        start_date_time="2026-09-22T14:15:00Z",
        end_date_time="2026-09-22T15:05:30Z",
        cdr_token={
            "country_code": "AR",
            "party_id": "EVP",
            "uid": "TOK-1",
            "type": "RFID",
            "contract_id": "C-1",
        },
        auth_method="AUTH_REQUEST",
        cdr_location={
            "id": "LOC-1",
            "address": "Av. x 1",
            "city": "Santiago",
            "country": "CHL",
            "coordinates": {"latitude": "-33.4", "longitude": "-70.6"},
            "evse_uid": "EVSE-1",
            "connector_id": "1",
            "connector_standard": "IEC_62196_T2_COMBO",
            "connector_format": "SOCKET",
            "connector_power_type": "DC",
        },
        currency="USD",
        charging_periods=[
            {"start_date_time": "2026-09-22T14:15:00Z", "dimensions": [{"type": "ENERGY", "volume": 10.0}]}
        ],
        total_cost={"excl_vat": 5.0, "incl_vat": 5.95},
        total_energy=10.0,
        total_time=0.5,
    )


@pytest.mark.asyncio
async def test_post_cdr_devuelve_el_cdr_creado(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/cdrs/CL/CHG/CDR-1",
        json=_envelope(SAMPLE_CDR),
        status_code=201,
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.post_cdr(
            "TOKEN_B_1", "CL", "CHG", "CDR-1", CdrInput(**_cdr_input_kwargs())
        )

    assert result.id == "CDR-1"
    assert result.total_cost.incl_vat == 5.95


@pytest.mark.asyncio
async def test_get_cdr_devuelve_un_cdr(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/cdrs/CL/CHG/CDR-1",
        json=_envelope(SAMPLE_CDR),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.get_cdr("TOKEN_B_1", "CL", "CHG", "CDR-1")

    assert result.id == "CDR-1"


@pytest.mark.asyncio
async def test_get_cdrs_lista_con_paginacion(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/cdrs?offset=0&limit=10",
        json=_envelope([SAMPLE_CDR]),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        page = await client.get_cdrs("TOKEN_B_1", offset=0, limit=10)

    assert page.total == 1
    assert page.cdrs[0].id == "CDR-1"


@pytest.mark.asyncio
async def test_post_cdr_repetido_lanza_ocpi_error_409(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/cdrs/CL/CHG/CDR-1",
        status_code=409,
        json=_envelope({}, status_code=2002, status_message="CDR ya existe (inmutable)."),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.post_cdr(
                "TOKEN_B_1", "CL", "CHG", "CDR-1", CdrInput(**_cdr_input_kwargs())
            )
