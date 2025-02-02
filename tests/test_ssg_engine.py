import pytest

from custom_components.price_tracker.services.ssg.engine import SsgEngine


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_ssg_parse_1():
    engine = SsgEngine(
        item_url="https://emart.ssg.com/item/itemView.ssg?itemId=2097001557433&siteNo=6001",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None
