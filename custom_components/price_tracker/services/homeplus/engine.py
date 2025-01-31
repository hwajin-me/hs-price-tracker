import re
from typing import Optional
from urllib.parse import unquote

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.homeplus.const import CODE, NAME
from custom_components.price_tracker.services.homeplus.parser import HomeplusParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 AU/0510ed03-e07e-41f4-9f63-90022dae21f2 HOMEPLUS/IOS/MOBILE/6.2.9"
_URL = "https://mfront.homeplus.co.kr/item?itemNo={}&storeType=HYPER&abtp=A_H_37_PD_068804218_1_1_068804656_CS001_"
_HEADERS = {
    "devicemodel": "iPhone15,2",
    "sec-fetch-site": "none",
    "sec-fetch-mode": "navigate",
    "sec-fetch-dest": "document",
}


class HomeplusEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = HomeplusEngine.parse_id(item_url)
        self._proxies = proxies
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData | None:
        request = SafeRequest(
            proxies=self._proxies,
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
        )
        request.accept_text_html()
        request.accept_encoding("gzip, deflate, br")
        request.cookie(key="domainType", value="mobile")
        request.user_agent(user_agent=_UA)
        response = await request.request(
            method=SafeRequestMethod.GET, url=_URL.format(self.id)
        )

        if response.is_not_found:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
            )

        logging_for_response(response, __name__, "homeplus")
        parser = HomeplusParser(html=response.data)

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
            url="https://mfront.homeplus.co.kr/item?itemNo={}&storeType=HYPER".format(
                self.id
            ),
            options=parser.options,
            inventory=parser.inventory_status,
        )

    def id_str(self) -> str:
        return "{}".format(self.id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"itemNo=(?P<item_no>\d+)", unquote(item_url))
        g = u.groupdict()

        if g is None:
            raise InvalidItemUrlError("Invalid homeplus item url {}".format(item_url))

        return g["item_no"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME

    def url(self) -> str:
        return self.item_url
