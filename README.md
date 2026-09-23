# latam-evra-ocpi

Cliente Python no oficial para el **Hub de roaming OCPI 2.3.0** de
[LATAM EV Roaming Alliance (LEA)](https://latam-evra.org).

> **Estado:** este paquete todavía **no está publicado en PyPI**. El Hub hoy
> solo implementa server-side el módulo **Credentials & Registration**; el
> resto de los módulos OCPI están tipados como stubs a la espera del
> roadmap del Hub (ver tabla más abajo).

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

## Módulos: disponibles vs roadmap

El Hub implementa OCPI 2.3.0 de forma incremental. Este SDK refleja ese
estado exactamente — no hay métodos que simulen funcionalidad no soportada
por el servidor.

| Módulo OCPI                     | Estado en el Hub    | Métodos del SDK                                              |
|----------------------------------|----------------------|---------------------------------------------------------------|
| Credentials & Registration       | ✅ Disponible        | `get_versions`, `get_details`, `register_credentials`, `renew_credentials`, `terminate_credentials` |
| Locations                        | ✅ Disponible        | `get_locations`, `get_location`, `put_location`, `patch_location` |
| Tariffs                          | ✅ Disponible        | `get_tariffs`, `get_tariff`, `put_tariff`, `delete_tariff` |
| Hub Client Info                  | ✅ Disponible        | `list_hub_client_info`, `get_hub_client_info` |
| Sessions                         | 🚧 Roadmap           | `get_active_session` → `NotImplementedError`                  |
| CDRs                             | 🚧 Roadmap           | `get_cdrs` → `NotImplementedError`                             |
| Tokens & Authorisation           | 🚧 Roadmap           | `authorize_token` → `NotImplementedError`                      |
| Commands                         | 🚧 Roadmap           | `send_command` → `NotImplementedError`                          |
| Invoice Reconciliation (Ed. 2)   | 🚧 Roadmap           | `get_invoice_reconciliation` → `NotImplementedError`            |
| Charging Profiles                | 🚧 Roadmap           | `set_charging_profile` → `NotImplementedError`                  |

Los modelos Pydantic de los módulos en roadmap (`latam_evra_ocpi.models`,
p. ej. `Location`, `Session`, `Cdr`, `Tariff`, `Token`, `HubClientInfo`,
`InvoiceReconciliation`, `ChargingProfileRequest`) ya están definidos a
partir de los payloads de ejemplo publicados en el Hub, para que el tipado
esté listo apenas cada módulo se implemente server-side. Cada método
lanza `OcpiModuleNotAvailableError` (subclase de `NotImplementedError`) con
un mensaje que referencia el roadmap (`docs/Roaming_hub_Latam.md` en el
repo del Hub).

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
