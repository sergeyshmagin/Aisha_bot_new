import pytest
from frontend_bot.services import transcript_cache
from frontend_bot.shared.redis_client import redis_client

@pytest.fixture(autouse=True)
async def cleanup_transcript_cache():
    await transcript_cache.clear()

@pytest.mark.asyncio
async def test_set_and_get():
    await transcript_cache.set(123, "/path/to/file1.txt")
    result = await transcript_cache.get(123)
    assert result == "/path/to/file1.txt"

@pytest.mark.asyncio
async def test_remove():
    await transcript_cache.set(456, "/path/to/file2.txt")
    await transcript_cache.remove(456)
    result = await transcript_cache.get(456)
    assert result is None

@pytest.mark.asyncio
async def test_clear():
    await transcript_cache.set(1, "a.txt")
    await transcript_cache.set(2, "b.txt")
    await transcript_cache.clear()
    assert await transcript_cache.get(1) is None
    assert await transcript_cache.get(2) is None

@pytest.mark.asyncio
async def test_all():
    await transcript_cache.set(10, "foo.txt")
    await transcript_cache.set(20, "bar.txt")
    all_items = await transcript_cache.all()
    assert all_items[10] == "foo.txt"
    assert all_items[20] == "bar.txt"
    assert len(all_items) == 2 