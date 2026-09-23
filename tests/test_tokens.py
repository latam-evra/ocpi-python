import pytest

from latam_evra_ocpi import OcpiClient
from latam_evra_ocpi.exceptions import OcpiError
from latam_evra_ocpi.models.tokens import TokenInput

BASE_URL = "https://hub.latam-evra.org/api/ocpi/2.3.0"

SAMPLE_TOKEN = {
    "country_code": "AR",
    "party_id": "EVP",
    "uid": "TOK-1",
    "type": "RFID",
    "contract_id": "C-1",
    "issuer": "LATAM EVP",
    "valid": True,
    "whitelist": "ALWAYS",
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
async def test_put_token_devuelve_el_token_creado(httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/tokens/AR/EVP/TOK-1",
        json=_envelope(SAMPLE_TOKEN),
        status_code=201,
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.put_token(
            "TOKEN_B_1",
            "AR",
            "EVP",
            "TOK-1",
            TokenInput(
                uid="TOK-1",
                type="RFID",
                contract_id="C-1",
                issuer="LATAM EVP",
                valid=True,
                whitelist="ALWAYS",
            ),
        )

    assert result.uid == "TOK-1"


@pytest.mark.asyncio
async def test_patch_token_hace_patch_parcial(httpx_mock):
    httpx_mock.add_response(
        method="PATCH",
        url=f"{BASE_URL}/tokens/AR/EVP/TOK-1",
        json=_envelope({**SAMPLE_TOKEN, "valid": False}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.patch_token("TOKEN_B_1", "AR", "EVP", "TOK-1", {"valid": False})

    assert result.valid is False


@pytest.mark.asyncio
async def test_get_token_devuelve_un_token(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/tokens/AR/EVP/TOK-1",
        json=_envelope(SAMPLE_TOKEN),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.get_token("TOKEN_B_1", "AR", "EVP", "TOK-1")

    assert result.uid == "TOK-1"


@pytest.mark.asyncio
async def test_get_tokens_lista_con_paginacion(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/tokens?offset=0&limit=10",
        json=_envelope([SAMPLE_TOKEN]),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        page = await client.get_tokens("TOKEN_B_1", offset=0, limit=10)

    assert page.total == 1
    assert page.tokens[0].uid == "TOK-1"


@pytest.mark.asyncio
async def test_delete_token_no_lanza_en_exito(httpx_mock):
    httpx_mock.add_response(
        method="DELETE",
        url=f"{BASE_URL}/tokens/AR/EVP/TOK-1",
        json=_envelope({}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        await client.delete_token("TOKEN_B_1", "AR", "EVP", "TOK-1")


@pytest.mark.asyncio
async def test_authorize_token_hace_post_con_location_references(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/tokens/AR/EVP/TOK-1/authorize",
        json=_envelope({"allowed": "ALLOWED"}),
        match_json={"location_id": "LOC-1"},
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.authorize_token(
            "TOKEN_B_1", "AR", "EVP", "TOK-1", {"location_id": "LOC-1"}
        )

    assert result.allowed == "ALLOWED"


@pytest.mark.asyncio
async def test_authorize_token_manda_body_vacio_por_defecto(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/tokens/AR/EVP/TOK-1/authorize",
        json=_envelope({"allowed": "ALLOWED"}),
        match_json={},
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.authorize_token("TOKEN_B_1", "AR", "EVP", "TOK-1")

    assert result.allowed == "ALLOWED"


@pytest.mark.asyncio
async def test_authorize_token_nunca_lanza_resuelve_a_blocked(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/tokens/AR/ZZZ/DOES-NOT-EXIST/authorize",
        json=_envelope({"allowed": "BLOCKED"}),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        result = await client.authorize_token("TOKEN_B_1", "AR", "ZZZ", "DOES-NOT-EXIST")

    assert result.allowed == "BLOCKED"


@pytest.mark.asyncio
async def test_get_token_lanza_ocpi_error_en_404(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/tokens/AR/EVP/DOES-NOT-EXIST",
        status_code=404,
        json=_envelope({}, status_code=2001, status_message="Token no encontrado."),
    )

    async with OcpiClient(base_url=BASE_URL) as client:
        with pytest.raises(OcpiError):
            await client.get_token("TOKEN_B_1", "AR", "EVP", "DOES-NOT-EXIST")
