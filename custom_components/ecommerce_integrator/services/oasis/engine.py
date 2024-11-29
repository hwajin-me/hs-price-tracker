import logging
import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.oasis.const import NAME, CODE
from custom_components.price_tracker.services.oasis.parser import OasisParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_LOGGER = logging.getLogger(__name__)
_URL = "https://m.oasis.co.kr/product/detail/{}"


class OasisEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = OasisEngine.parse_id(item_url)
        self.product_id = self.id
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData:
        request = SafeRequest(
            proxies=self._proxies,
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
        )
        response = await request.request(
            method=SafeRequestMethod.GET, url=_URL.format(self.product_id)
        )
        oasis_parser = OasisParser(text=response.data)
        logging_for_response(response, __name__)

        return ItemData(
            id=self.product_id,
            brand=oasis_parser.brand,
            name=oasis_parser.name,
            description=oasis_parser.description,
            category=oasis_parser.category,
            price=oasis_parser.price,
            delivery=oasis_parser.delivery,
            image=oasis_parser.image,
            url=self.item_url,
            inventory=oasis_parser.inventory,
            unit=oasis_parser.unit,
            options=oasis_parser.options,
        )

    def id_str(self) -> str:
        return self.product_id

    @staticmethod
    def parse_id(item_url: str):
        m = re.search(r"(?P<product_id>[\d\-]+)(?:$|\?.*?$)", item_url)

        if m is None:
            raise InvalidItemUrlError("Invalid OASIS Product URL {}".format(item_url))
        g = m.groupdict()

        if "product_id" not in g:
            raise InvalidItemUrlError("Invalid OASIS Product URL {}".format(item_url))

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
