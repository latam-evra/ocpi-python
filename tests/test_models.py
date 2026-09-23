"""Sanity checks de los modelos Pydantic de los módulos en roadmap."""

from latam_evra_ocpi.models import Cdr, Location, Tariff


def test_location_model_from_sample_payload():
    location = Location.model_validate(
        {
            "country_code": "CL",
            "party_id": "CHG",
            "id": "LOC-SANTIAGO-01",
            "publish": True,
            "address": "Av. Andrés Bello 2425",
            "city": "Santiago",
            "country": "CHL",
            "coordinates": {"latitude": "-33.4182", "longitude": "-70.6061"},
            "name": "Estación Hub Providencia",
            "evses": [{"uid": "EVSE-0123", "status": "AVAILABLE"}],
        }
    )
    assert location.evses[0].status == "AVAILABLE"
    assert location.id == "LOC-SANTIAGO-01"


def test_tariff_model_from_sample_payload():
    tariff = Tariff.model_validate(
        {
            "id": "TAR-FAST-DC-2026",
            "country_code": "CL",
            "party_id": "CHG",
            "currency": "USD",
            "elements": [
                {
                    "price_components": [
                        {"type": "ENERGY", "price": 0.35, "vat": 19.0, "step_size": 1}
                    ]
                }
            ],
        }
    )
    assert tariff.elements[0].price_components[0].price == 0.35
    assert tariff.id == "TAR-FAST-DC-2026"


def test_cdr_model_from_docs_sample():
    cdr = Cdr.model_validate(
        {
            "country_code": "CL",
            "party_id": "CHG",
            "id": "CDR-LATAM-2026-008912",
            "start_date_time": "2026-09-22T14:15:00Z",
            "end_date_time": "2026-09-22T15:05:30Z",
            "session_id": "SES-98234-LATAM",
            "cdr_token": {
                "country_code": "AR",
                "party_id": "EVP",
                "uid": "RFID-LATAM-98741",
                "type": "RFID",
                "contract_id": "AR-EVP-C00912",
            },
            "auth_method": "AUTH_REQUEST",
            "authorization_reference": "AUTH-REF-883921",
            "cdr_location": {
                "id": "LOC-SANTIAGO-01",
                "name": "Estación Hub Providencia",
                "address": "Av. Andrés Bello 2425",
                "city": "Santiago",
                "postal_code": "7500000",
                "country": "CHL",
                "coordinates": {"latitude": "-33.4182", "longitude": "-70.6061"},
                "evse_id": "CL*CHG*E0123*1",
                "evse_uid": "EVSE-0123",
                "connector_id": "1",
                "connector_standard": "IEC_62196_T2_COMBO",
                "connector_format": "SOCKET",
                "connector_power_type": "DC",
            },
            "currency": "USD",
            "tariffs": [],
            "charging_periods": [
                {
                    "start_date_time": "2026-09-22T14:15:00Z",
                    "dimensions": [
                        {"type": "ENERGY", "volume": 32.45},
                        {"type": "TIME", "volume": 0.842},
                    ],
                }
            ],
            "total_cost": {"excl_vat": 12.86, "incl_vat": 15.30},
            "total_fixed_cost": {"excl_vat": 1.50, "incl_vat": 1.785},
            "total_energy": 32.45,
            "total_energy_cost": {"excl_vat": 11.36, "incl_vat": 13.515},
            "total_time": 0.842,
            "total_time_cost": {"excl_vat": 0.0, "incl_vat": 0.0},
            "last_updated": "2026-09-22T15:06:00Z",
        }
    )
    assert cdr.total_cost.incl_vat == 15.30
    assert cdr.cdr_location.evse_id == "CL*CHG*E0123*1"
