"""Confirma que Charging Profiles (único módulo en roadmap) lanza
NotImplementedError con mensaje claro."""

import pytest

from latam_evra_ocpi.exceptions import OcpiModuleNotAvailableError


@pytest.mark.asyncio
async def test_set_charging_profile_not_implemented(client):
    with pytest.raises(NotImplementedError, match="Charging Profiles"):
        await client.set_charging_profile("SES-98234-LATAM")


def test_error_message_mentions_roadmap_doc():
    exc = OcpiModuleNotAvailableError("Locations")
    assert "roadmap" in str(exc)
    assert "docs/Roaming_hub_Latam.md" in str(exc)
