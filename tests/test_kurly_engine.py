import pytest

from custom_components.price_tracker.services.kurly.engine import KurlyEngine
from custom_components.price_tracker.services.ssg.engine import SsgEngine


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_kurly_parse_1():
    engine = KurlyEngine(
        item_url="https://www.kurly.com/goods/5159822",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None
