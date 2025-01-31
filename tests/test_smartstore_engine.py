import pytest
from curl_cffi import requests

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
        item_url="https://m.smartstore.naver.com/spcorp/products/11144528884",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.hookimpl(trylast=True)
def test_naver_smartstore_parse_3():
    r = requests.get(
        "https://m.smartstore.naver.com/spcorp/products/11144528884",
        impersonate="chrome",
    )

    assert r is not None
