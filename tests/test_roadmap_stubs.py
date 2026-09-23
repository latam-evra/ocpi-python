"""Confirma que los módulos en roadmap lanzan NotImplementedError con mensaje claro."""

import pytest

from latam_evra_ocpi.exceptions import OcpiModuleNotAvailableError


@pytest.mark.asyncio
async def test_get_active_session_not_implemented(client):
    with pytest.raises(NotImplementedError, match="Sessions"):
        await client.get_active_session("SES-98234-LATAM")


@pytest.mark.asyncio
async def test_get_cdrs_not_implemented(client):
    with pytest.raises(NotImplementedError, match="CDRs"):
        await client.get_cdrs()


@pytest.mark.asyncio
async def test_authorize_token_not_implemented(client):
    with pytest.raises(NotImplementedError, match="Tokens & Authorisation"):
        await client.authorize_token("RFID-LATAM-98741")


@pytest.mark.asyncio
async def test_send_command_not_implemented(client):
    with pytest.raises(NotImplementedError, match="Commands"):
        await client.send_command("START_SESSION")


@pytest.mark.asyncio
async def test_get_invoice_reconciliation_not_implemented(client):
    with pytest.raises(NotImplementedError, match="Invoice Reconciliation"):
        await client.get_invoice_reconciliation()


@pytest.mark.asyncio
async def test_set_charging_profile_not_implemented(client):
    with pytest.raises(NotImplementedError, match="Charging Profiles"):
        await client.set_charging_profile("SES-98234-LATAM")


def test_error_message_mentions_roadmap_doc():
    exc = OcpiModuleNotAvailableError("Locations")
    assert "roadmap" in str(exc)
    assert "docs/Roaming_hub_Latam.md" in str(exc)
