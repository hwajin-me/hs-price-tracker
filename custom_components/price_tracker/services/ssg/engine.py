import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
    NotFoundError,
)
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.ssg.const import CODE, NAME
from custom_components.price_tracker.services.ssg.parser import SsgParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_URL = "https://m.apps.ssg.com/appApi/itemView.ssg"
_ITEM_LINK = "https://emart.ssg.com/item/itemView.ssg?itemId={}&siteNo={}"


class SsgEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = SsgEngine.parse_id(item_url)
        self.product_id = self.id["product_id"]
        self.site_no = self.id["site_no"]
        self._proxy = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData:
        request = SafeRequest(
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
            proxies=self._proxy,
        )

        response = await request.request(
            method=SafeRequestMethod.POST,
            data={
                "params": {
                    "dispSiteNo": str(self.site_no),
                    "itemId": str(self.product_id),
                }
            },
            url=_URL,
        )

        text = response.data

        if response.is_not_found or not response.has:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.product_id),
                status=ItemStatus.DELETED,
            )

        logging_for_response(text, __name__, "ssg")

        try:
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
        except NotFoundError:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.product_id),
                status=ItemStatus.DELETED,
            )
        except Exception as e:
            raise e

    def id_str(self) -> str:
        return "{}_{}".format(self.product_id, self.site_no)

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
