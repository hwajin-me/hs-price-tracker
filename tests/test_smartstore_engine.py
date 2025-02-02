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

    assert r.status_code is 200


@pytest.mark.asyncio
@pytest.hookimpl(trylast=True)
async def test_naver_smartstore_parse_4():
    engine = SmartstoreEngine(
        item_url="https://smartstore.naver.com/farmforlife/products/8916619763",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.mark.asyncio
@pytest.hookimpl(trylast=True)
async def test_naver_smartstore_parse_5():
    engine = SmartstoreEngine(
        item_url="https://smartstore.naver.com/nsm33313140/products/10134655507",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.mark.asyncio
@pytest.hookimpl(trylast=True)
async def test_naver_smartstore_parse_6():
    engine = SmartstoreEngine(
        item_url="https://smartstore.naver.com/vitaair/products/7229371652",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.mark.asyncio
@pytest.hookimpl(trylast=True)
async def test_naver_smartstore_parse_7():
    engine = SmartstoreEngine(
        item_url="https://smartstore.naver.com/spcorp/products/640141319",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.mark.asyncio
@pytest.hookimpl(trylast=True)
async def test_naver_smartstore_parse_8():
    engine = SmartstoreEngine(
        item_url="https://smartstore.naver.com/heungbumall/products/278968704",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.mark.asyncio
@pytest.hookimpl(trylast=True)
async def test_naver_smartstore_parse_9():
    engine = SmartstoreEngine(
        item_url="https://smartstore.naver.com/nsm33313140/products/10134655507",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None


@pytest.mark.asyncio
@pytest.hookimpl(trylast=True)
async def test_naver_smartstore_parse_10():
    engine = SmartstoreEngine(
        item_url="https://brand.naver.com/syfoodshop/products/6040758245",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None
