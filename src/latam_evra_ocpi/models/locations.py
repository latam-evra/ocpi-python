from __future__ import annotations

from pydantic import BaseModel


class GeoCoordinates(BaseModel):
    latitude: str
    longitude: str


class Connector(BaseModel):
    id: str
    standard: str
    format: str
    power_type: str
    max_voltage: int
    max_amperage: int
    max_electric_power: int | None = None
    tariff_ids: list[str] | None = None


class Evse(BaseModel):
    uid: str
    evse_id: str | None = None
    status: str
    connectors: list[Connector] = []


class LocationInput(BaseModel):
    id: str
    publish: bool
    address: str
    city: str
    country: str
    coordinates: GeoCoordinates
    name: str | None = None
    evses: list[Evse] | None = None


class Location(BaseModel):
    country_code: str
    party_id: str
    id: str
    publish: bool
    address: str
    city: str
    country: str
    coordinates: GeoCoordinates
    name: str | None = None
    evses: list[Evse] = []


class LocationsPage(BaseModel):
    locations: list[Location]
    total: int
