import asyncio
import re
import uuid
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.iherb.const import CODE, NAME
from custom_components.price_tracker.services.iherb.parser import IherbParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
    bot_agents,
)
from custom_components.price_tracker.utilities.utils import random_bool

_URL = "https://catalog.app.iherb.com/product/{}"


class IherbEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = IherbEngine.parse_id(item_url)
        self._proxies = proxies
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData | None:
        request = SafeRequest(
            proxies=self._proxies,
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
        )
        # TODO: Prevent bot captcha
        request.accept_text_html()
        request.accept_language(language="ko-KR,en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5")
        request.accept_encoding("gzip, deflate, br")
        request.cache_control("no-cache")
        request.keep_alive()
        request.priority_u()
        request.pragma_no_cache()
        request.referer_no_referrer()
        request.sec_fetch_user('?1')
        request.sec_fetch_site('none')
        request.sec_fetch_mode_navigate()
        request.sec_fetch_dest_document()
        request.header(key="Host", value="catalog.app.iherb.com")
        request.cookie(
            key="ih-preference", value="country=KR&language=ko-KR&currency=KRW"
        )
        request.cookie(key="iher-pref1", value="sccode=KR&lan=ko-KR&scurcode=KRW")
        request.cookie(key="iher-pref2", value="sccode=KR&lan=en-US&scurcode=KRW")
        await request.user_agent(mobile_random=True, pc_random=True)
        await request.reuse_session(True)

        await request.request(
            method=SafeRequestMethod.GET, url='https://kr.iherb.com/pr/{}'.format(self.id), retain_cookie=True
        )
        await asyncio.sleep(0.5)
        response = await request.request(
            method=SafeRequestMethod.GET, url=_URL.format(self.id), retain_cookie=True
        )

        logging_for_response(response, __name__, "iherb")

        if not response.has:
            return None

        parser = IherbParser(data=response.data)

        return ItemData(
            id=self.id_str(),
            brand=parser.brand,
            name=parser.name,
            price=parser.price,
            description=parser.description,
            category=parser.category,
            delivery=parser.delivery,
            unit=parser.unit,
            image=parser.image,
            options=parser.options,
            url=parser.url,
            inventory=parser.inventory_status,
        )

    def id_str(self) -> str:
        return "{}".format(self.id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"/(?P<id>\d+)(?:/|)", item_url)

        if u is None:
            raise InvalidItemUrlError("Invalid iherb item url {}".format(item_url))

        g = u.groupdict()

        if g is None:
            raise InvalidItemUrlError("Invalid iherb item url {}".format(item_url))

        return g["id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME

    def url(self) -> str:
        return self.item_url
