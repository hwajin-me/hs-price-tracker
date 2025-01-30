import pytest

from custom_components.price_tracker.services.smartstore.engine import SmartstoreEngine


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_naver_smartstore_parse_1():
    engine = SmartstoreEngine(
        item_url="https://m.brand.naver.com/hbafstore/products/9132075573",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_naver_smartstore_parse_2():
    engine = SmartstoreEngine(
        item_url="https://smartstore.naver.com/spcorp/products/11144528884",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None
