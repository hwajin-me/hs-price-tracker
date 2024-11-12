import json
import logging
import re

import aiohttp

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidError, InvalidItemUrlError
from custom_components.price_tracker.datas.delivery import DeliveryData, DeliveryPayType
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.kurly.const import NAME, CODE
from custom_components.price_tracker.services.kurly.parser import KurlyParser
from custom_components.price_tracker.utilities.request import default_request_headers

_LOGGER = logging.getLogger(__name__)
_AUTH_URL = "https://www.kurly.com/nx/api/session"
_URL = "https://api.kurly.com/showroom/v2/products/{}"
_ITEM_LINK = "https://www.kurly.com/goods/{}"


class KurlyEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        self.id = KurlyEngine.parse_id(item_url)

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(verify_ssl=False)
            ) as session:
                async with session.get(
                        url=_AUTH_URL, headers={**default_request_headers()}
                ) as auth:
                    auth_result = await auth.read()

                    if auth.status == 200:
                        auth_data = json.loads(auth_result)
                        async with session.get(
                                url=_URL.format(self.id),
                                headers={
                                    **default_request_headers(),
                                    "Authorization": "Bearer {}".format(
                                        auth_data["accessToken"]
                                    ),
                                },
                        ) as response:
                            result = await response.text()

                            if response.status == 200:
                                j = json.loads(result)
                                kurly_parser = KurlyParser(text=result)
                                d = j["data"]

                                _LOGGER.debug("Kurly Response", d)

                                return ItemData(
                                    id=d["no"],
                                    name=d["name"],
                                    price=kurly_parser.price,
                                    image=d["main_image_url"],
                                    description=d["short_description"],
                                    category=d["category_ids"].join(">"),
                                    delivery=DeliveryData(
                                        price=0.0,
                                        pay_type=DeliveryPayType.FREE
                                        if d["is_direct_order"]
                                        else DeliveryPayType.PAID,
                                    ),
                                    url=_ITEM_LINK.format(d["no"]),
                                    inventory=InventoryStatus.IN_STOCK
                                    if not d["is_sold_out"]
                                    else InventoryStatus.OUT_OF_STOCK,
                                )
                            else:
                                _LOGGER.error("Kurly Fetch Request Error", response)
                    else:
                        _LOGGER.error("Kurly Authentication Request Error")

        except Exception:
            _LOGGER.exception("Kurly Request Error")

    def id(self) -> str:
        return self.id

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"(?:goods|products)/(?P<product_id>[\d]+)", item_url)

        if u is None:
            raise InvalidItemUrlError("Bad Kurly item_url {}.".format(item_url))

        g = u.groupdict()

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
