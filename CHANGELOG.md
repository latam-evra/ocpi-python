# Changelog

Todas las versiones notables de `latam-evra-ocpi` se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/) y
este proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [0.5.0] - 2026-09-23

### Agregado

- Charging Profiles implementado de verdad contra el Hub
  (`get_active_charging_profile()`, `set_charging_profile()`,
  `delete_charging_profile()`, `get_charging_profile()`). Reemplaza el
  stub `set_charging_profile(session_id)` que lanzaba
  `OcpiModuleNotAvailableError` (breaking change de firma). Al igual
  que Commands, no es CRUD simétrico: un método por acción (GET/PUT/
  DELETE) sobre una sesión existente, más `get_charging_profile()` cuyo
  GET vive en `/chargingprofiles/callback/{id}`.
- Nuevo módulo `latam_evra_ocpi.models.charging_profiles`, reemplazando
  el `ChargingProfile`/`ChargingProfileRequest` simplificado que vivía
  en `models.stubs` (retirado) — `ChargingProfile.limit` (único límite)
  se reemplaza por `charging_profile_period` (lista de
  `{start_period, limit}`), reflejando el objeto OCPI 2.3.0 real.

### Quitado

- Con Charging Profiles implementado, ya no queda ningún módulo en el
  roadmap del Hub: se elimina `OcpiModuleNotAvailableError` de
  `exceptions.py`.

## [0.4.0] - 2026-09-23

### Agregado

- Sessions, CDRs, Tokens & Authorisation, Commands e Invoice
  Reconciliation implementados de verdad contra el Hub. Reemplazan los
  stubs que lanzaban `OcpiModuleNotAvailableError` (breaking change de
  firma en todos los métodos afectados).
- Commands es el módulo más asimétrico: sin `send_command` genérico, 5
  métodos tipados (uno por `command_type`) más `get_command()`, cuyo
  GET vive en `/commands/callback/{id}`, no en `/commands/{type}`.
- Tokens gana `authorize_token()` como método standalone, separado de
  su CRUD.
- CDRs es solo-POST (inmutable); Invoice Reconciliation es solo-PUT
  (sin POST) — no confundir pese a la similitud superficial.

## [0.3.0] - 2026-09-23

### Agregado

- Hub Client Info implementado de verdad contra el Hub
  (`list_hub_client_info(token_b, offset, limit)`,
  `get_hub_client_info(token_b, country_code, party_id)`). Reemplaza el
  stub `get_hub_client_info()` de versiones anteriores (breaking change
  de firma).
- Nuevo módulo `latam_evra_ocpi.models.hub_client_info` con
  `HubClientInfoEntry`/`HubClientInfoPage`, reemplazando el
  `HubClientInfo` simplificado que vivía en `models.stubs` — status
  ahora incluye `STOPPED` (antes solo `CONNECTED`/`OFFLINE`/`PLANNED`/
  `SUSPENDED`, sin mapear el `TERMINATED` real del Hub) y se agregan
  `role`/`last_updated`.
- Suite de tests de integración para Hub Client Info
  (`tests/integration/test_hub_client_info_integration.py`).

## [0.2.0] - 2026-09-23

### Agregado

- Locations y Tariffs implementados de verdad contra el Hub
  (`get_locations`, `get_location`, `put_location`, `patch_location`,
  `get_tariffs`, `get_tariff`, `put_tariff`, `delete_tariff`).
  Reemplazan los stubs genéricos de la v0.1.0 (breaking change de
  firma).

### Conocido

- `get_locations`/`get_tariffs` no exponen aún el total real que
  devuelve el Hub vía el header `X-Total-Count` — `total` es
  aproximado al tamaño de la página actual.

## [0.1.0] - 2026-09-22

### Agregado

- Cliente async `OcpiClient` (basado en `httpx`) para el módulo
  **Credentials & Registration** del Hub OCPI 2.3.0 de LATAM EV Roaming
  Alliance — el único módulo implementado server-side hoy:
  - `get_versions()` — `GET /versions`.
  - `get_details()` — `GET /details`.
  - `register_credentials(token_a, url, roles)` — `POST /credentials`
    (handshake inicial).
  - `renew_credentials(token_b)` — `PUT /credentials`.
  - `terminate_credentials(token_b)` — `DELETE /credentials`.
- Modelos tipados con Pydantic v2 para el sobre OCPI (`OcpiResponse[T]`),
  roles (`CredentialsRole`), y las respuestas de cada endpoint.
- Excepción `OcpiError` (expone `status_code` / `status_message` /
  `http_status`) para errores reportados dentro del sobre OCPI, siguiendo
  las constantes de `OCPI_STATUS` (réplica de `lib/ocpi/response.ts` del
  Hub).
- Stubs tipados para los 8 módulos del roadmap (Locations, Sessions, CDRs,
  Tariffs, Tokens & Authorisation, Commands, Hub Client Info, Invoice
  Reconciliation, Charging Profiles): cada método lanza
  `OcpiModuleNotAvailableError` (subclase de `NotImplementedError`) con un
  mensaje claro. Los modelos Pydantic de estos módulos ya están definidos en
  `latam_evra_ocpi.models`, listos para cuando el Hub los soporte.
- Suite de tests con `pytest` + `pytest-httpx` cubriendo éxito y errores del
  handshake de Credentials, y confirmando que cada stub de roadmap lanza
  `NotImplementedError`.
