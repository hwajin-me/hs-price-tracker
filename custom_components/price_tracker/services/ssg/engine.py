import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.ssg.const import CODE, NAME
from custom_components.price_tracker.services.ssg.parser import SsgParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.request import http_request

_URL = "https://m.apps.ssg.com/appApi/itemView.ssg"
_ITEM_LINK = "https://emart.ssg.com/item/itemView.ssg?itemId={}&siteNo={}"


class SsgEngine(PriceEngine):
    def __init__(self, item_url: str, device: None = None, proxy: Optional[str] = None):
        self.item_url = item_url
        self.id = SsgEngine.parse_id(item_url)
        self.product_id = self.id["product_id"]
        self.site_no = self.id["site_no"]
        self._proxy = proxy
        self._device = device

    async def load(self) -> ItemData:
        response = await http_request(
            method="post",
            json={
                "params": {
                    "dispSiteNo": str(self.site_no),
                    "itemId": str(self.product_id),
                }
            },
            url=_URL,
            skip_auto_headers=[],
        )

        text = response["data"]
        logging_for_response(text, __name__, "ssg")
        ssg_parser = SsgParser(text)

        return ItemData(
            id=self.product_id,
            brand=ssg_parser.brand,
            name=ssg_parser.name,
            price=ssg_parser.price,
            description=ssg_parser.description,
            url=ssg_parser.url,
            image=ssg_parser.image,
            category=ssg_parser.category,
            inventory=ssg_parser.inventory_status,
            delivery=ssg_parser.delivery,
            unit=ssg_parser.unit,
        )

    def id(self) -> str:
        return "{}_{}".format(self.product_id, self.site_no)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(
            r"itemId=(?P<product_id>[\d]+)&siteNo=(?P<site_no>[\d]+)", item_url
        )

        if u is None:
            raise InvalidItemUrlError("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data["product_id"] = g["product_id"]
        data["site_no"] = g["site_no"]

        return data

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
