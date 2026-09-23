import pytest_asyncio

from latam_evra_ocpi import OcpiClient

BASE_URL = "https://hub.test/api/ocpi/2.3.0"


@pytest_asyncio.fixture
async def client():
    async with OcpiClient(base_url=BASE_URL) as c:
        yield c
