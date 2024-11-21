import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.coupang.const import NAME, CODE
from custom_components.price_tracker.services.coupang.parser import CoupangParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_URL = "https://m.coupang.com/vm/products/{}?itemId={}&vendorItemId={}"
_ITEM_LINK = "https://www.coupang.com/vp/products/{}?itemId={}&vendorItemId={}"


class CoupangEngine(PriceEngine):
    def __init__(
        self, item_url: str, device: None = None, proxies: Optional[list] = None
    ):
        self.item_url = item_url
        self.id = CoupangEngine.parse_id(item_url)
        self.product_id = self.id["product_id"]
        self.item_id = self.id["item_id"]
        self.vendor_item_id = self.id["vendor_item_id"]
        self._proxy = proxies
        self._device = device

    async def load(self) -> ItemData:
        request = SafeRequest()
        await request.user_agent(mobile_random=True)
        request.proxies(self._proxy)
        response = await request.request(
            method=SafeRequestMethod.GET,
            url=_URL.format(self.product_id, self.item_id, self.vendor_item_id),
        )
        data = response.data
        coupang_parser = CoupangParser(text=data)
        logging_for_response(data, __name__, "coupang")

        return ItemData(
            id=self.id_str(),
            name=coupang_parser.name,
            description=coupang_parser.description,
            brand=coupang_parser.brand,
            price=coupang_parser.price,
            image=coupang_parser.image,
            category=coupang_parser.category,
            url=_ITEM_LINK.format(self.product_id, self.item_id, self.vendor_item_id),
            options=coupang_parser.options,
            unit=coupang_parser.unit,
            inventory=coupang_parser.inventory,
            delivery=coupang_parser.delivery,
        )

    def id_str(self) -> str:
        return "{}_{}_{}".format(self.product_id, self.item_id, self.vendor_item_id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(
            r"products\/(?P<product_id>\d+)\?itemId=(?P<item_id>[\d]+).*?(?:|vendorItemId=(?P<vendor_item_id>[\d]+).*)$",
            item_url,
        )

        if u is None:
            raise InvalidItemUrlError("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data["product_id"] = g["product_id"]
        data["item_id"] = g["item_id"]
        data["vendor_item_id"] = ""
        if "vendor_item_id" in g:
            data["vendor_item_id"] = g["vendor_item_id"]
        return data

    @staticmethod
    def engine_name() -> str:
        return NAME

    @staticmethod
    def engine_code() -> str:
        return CODE

    def url(self) -> str:
        return _ITEM_LINK.format(self.product_id, self.item_id, self.vendor_item_id)
