import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app

TEST_URL_PREFIX = "https://example.com/pytest/"

def unique_url() -> str:
    return f"{TEST_URL_PREFIX}{uuid.uuid4()}"

@pytest_asyncio.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
        await app.state.db_pool.execute(
            "DELETE FROM urls WHERE long_url LIKE $1", f"{TEST_URL_PREFIX}%"
        )

@pytest.mark.asyncio
async def test_shorten_then_redirect(client):
    long_url = unique_url()

    post = await client.post("/shorten", json={"url": long_url})
    assert post.status_code == 200
    short_code = post.json()["short_code"]

    get = await client.get(f"/{short_code}")
    assert get.status_code == 302
    assert get.headers["location"] == long_url

@pytest.mark.asyncio
async def test_duplicate_url_returns_same_code(client):
    long_url = unique_url()

    first = await client.post("/shorten", json={"url": long_url})
    second = await client.post("/shorten", json={"url": long_url})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["short_code"] == second.json()["short_code"]

@pytest.mark.asyncio
async def test_unknown_code_returns_404(client):
    response = await client.get(f"/{uuid.uuid4().hex[:6]}")
    assert response.status_code == 404