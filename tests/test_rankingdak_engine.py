import pytest
from curl_cffi import requests

from custom_components.price_tracker.services.rankingdak.engine import RankingdakEngine
from custom_components.price_tracker.services.smartstore.engine import SmartstoreEngine


@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_rankingdak_parse_1():
    engine = RankingdakEngine(
        item_url="https://www.rankingdak.com/product/view?productCd=f000000991",
    )
    result = await engine.load()
    assert result is not None
    assert result.name is not None
