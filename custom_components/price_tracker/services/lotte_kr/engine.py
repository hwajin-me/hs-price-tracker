import re
from typing import Optional
from urllib.parse import unquote

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.lotte_kr.const import CODE, NAME
from custom_components.price_tracker.services.lotte_kr.parser import LotteOnParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_URL = (
    "https://pbf.lotteon.com/product/v2/detail/search/base/pd/{}?detailType=BNDL_SPDP"
)
_DISCOUNT_URL = "https://pbf.lotteon.com/product/v1/detail/promotion/promotionQtyChangeFavorInfoList"


class LotteOnEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = LotteOnEngine.parse_id(item_url)
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
        request.user_agent(mobile_random=True)
        response = await request.request(
            method=SafeRequestMethod.GET, url=_URL.format(self.id)
        )

        if response.is_not_found:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
            )

        logging_for_response(response, __name__, "lotte_on")

        pre_parse = LotteOnParser(data=response.data)

        discount_response = await request.request(
            method=SafeRequestMethod.POST,
            url=_DISCOUNT_URL,
            data=pre_parse.discount_params,
        )

        logging_for_response(response, __name__, "lotte_on")

        parser = LotteOnParser(data=response.data, discount=discount_response.data)

        return ItemData(
            id=self.id_str(),
            brand=parser.brand,
            name=parser.name,
            price=parser.price,
            description=parser.description,
            category=parser.category,
            delivery=parser.delivery,
            unit=parser.unit,
            url="https://www.lotteon.com/p/product/{}".format(self.id),
            image=parser.image,
            options=parser.options,
            inventory=parser.inventory_status,
        )

    def id_str(self) -> str:
        return "{}".format(self.id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"product/(?P<id>\w+)", unquote(item_url))
        g = u.groupdict()

        if g is None:
            raise InvalidItemUrlError("Invalid Lotte ON item url {}".format(item_url))

        return g["id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME

    def url(self) -> str:
        return self.item_url
