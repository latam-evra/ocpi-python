# latam-evra-ocpi

Cliente Python no oficial para el **Hub de roaming OCPI 2.3.0** de
[LATAM EV Roaming Alliance (LEA)](https://latam-evra.org).

> **Estado:** este paquete todavía **no está publicado en PyPI**. El Hub
> implementa server-side todos los módulos del roadmap OCPI 2.3.0 (ver
> tabla más abajo).

## Instalación

Mientras el paquete no esté en PyPI, instalalo directamente desde este
repositorio:

```bash
pip install -e sdks/python
```

Cuando se publique en PyPI, la instalación será simplemente:

```bash
pip install latam-evra-ocpi
```

Requiere Python 3.9+. Dependencias runtime: [`httpx`](https://www.python-httpx.org/)
y [`pydantic`](https://docs.pydantic.dev/) v2.

Para desarrollo (tests):

```bash
pip install -e "sdks/python[dev]"
pytest sdks/python
```

## Uso: handshake de Credentials completo

El flujo de Credentials & Registration conecta un CSMS (CPO o eMSP) al Hub:
el CSMS recibe un `TOKEN_A` de un administrador del Hub (fuera de banda),
y lo usa para registrarse. El Hub responde con un `TOKEN_B` que el CSMS debe
guardar de forma segura para llamadas futuras (`PUT`/`DELETE`).

```python
import asyncio

from latam_evra_ocpi import OcpiClient, OcpiError


async def main() -> None:
    async with OcpiClient(base_url="https://latam-evra.org/api/ocpi/2.3.0") as client:
        # 1. Descubrir qué versiones y endpoints soporta el Hub.
        versions = await client.get_versions()
        details = await client.get_details()
        print("Versiones soportadas:", [v.version for v in versions])
        print("Endpoints del Hub:", [e.identifier for e in details.endpoints])

        # 2. Registrar credenciales con el TOKEN_A recibido del admin del Hub.
        try:
            credentials = await client.register_credentials(
                token_a="TOKEN_A_RECIBIDO_DEL_ADMIN",
                url="https://mi-csms.example.com/ocpi/versions",
                roles=[{"role": "CPO", "party_id": "CHG", "country_code": "CL"}],
            )
        except OcpiError as exc:
            # El Hub responde 200 OK con un status_code de error dentro del sobre.
            print(f"Error OCPI {exc.status_code}: {exc.status_message}")
            return

        token_b = credentials.token
        print("Handshake completo. TOKEN_B:", token_b)

        # 3. Más adelante: renovar el TOKEN_B.
        renewed = await client.renew_credentials(token_b=token_b)
        token_b = renewed.token

        # 4. O terminar la conexión.
        await client.terminate_credentials(token_b=token_b)


asyncio.run(main())
```

### Manejo de errores

El Hub siempre responde con el sobre estándar OCPI
(`{ data, status_code, status_message, timestamp }`). Cuando `status_code`
no es `1000` (éxito), el cliente lanza `OcpiError`, que expone:

- `status_code`: código OCPI (`OCPI_STATUS.UNKNOWN_TOKEN`, etc.)
- `status_message`: mensaje humano devuelto por el Hub
- `http_status`: código HTTP de la respuesta

```python
from latam_evra_ocpi import OCPI_STATUS, OcpiError

try:
    await client.register_credentials(token_a="invalido", url="...", roles=[...])
except OcpiError as exc:
    if exc.status_code == OCPI_STATUS.UNKNOWN_TOKEN:
        print("TOKEN_A inválido o ya usado")
```

## Módulos disponibles

Todos los módulos del roadmap OCPI 2.3.0 del Hub están implementados de
verdad, tanto server-side como en este SDK.

| Módulo OCPI                     | Métodos del SDK                                              |
|----------------------------------|---------------------------------------------------------------|
| Credentials & Registration       | `get_versions`, `get_details`, `register_credentials`, `renew_credentials`, `terminate_credentials` |
| Locations                        | `get_locations`, `get_location`, `put_location`, `patch_location` |
| Tariffs                          | `get_tariffs`, `get_tariff`, `put_tariff`, `delete_tariff` |
| Hub Client Info                  | `list_hub_client_info`, `get_hub_client_info` |
| Sessions                         | `get_sessions`, `get_session`, `put_session`, `patch_session` |
| CDRs                             | `get_cdrs`, `get_cdr`, `post_cdr` |
| Tokens & Authorisation           | `get_tokens`, `get_token`, `put_token`, `patch_token`, `delete_token`, `authorize_token` |
| Commands                         | `start_session`, `reserve_now`, `stop_session`, `unlock_connector`, `cancel_reservation`, `get_command` |
| Charging Profiles                | `get_active_charging_profile`, `set_charging_profile`, `delete_charging_profile`, `get_charging_profile` |
| Invoice Reconciliation (Ed. 2)   | `get_invoice_reconciliations`, `get_invoice_reconciliation`, `put_invoice_reconciliation`, `delete_invoice_reconciliation` |

Consultá `docs/Roaming_hub_Latam.md` y `components/ModuleAccordion.tsx` en
el repositorio del Hub para el detalle de cada módulo.

## Tests de integración

Requieren el Hub real corriendo (`npm run dev` desde la raíz del repo,
o `pm2 restart latam-evra`). Se corren aparte de la suite normal:

```bash
.venv/bin/pytest -m integration tests/integration
```

Apuntan por defecto a `http://localhost:3947`; sobreescribir con
`OCPI_HUB_TEST_URL` si hace falta.

## Desarrollo

```bash
cd sdks/python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Licencia

MIT.
