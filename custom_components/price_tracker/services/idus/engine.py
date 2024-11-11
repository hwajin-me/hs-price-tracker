import json
import logging
import re

import aiohttp

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidError
from custom_components.price_tracker.datas.delivery import DeliveryData
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.datas.unit import ItemUnitData
from custom_components.price_tracker.utilities.request import default_request_headers

_LOGGER = logging.getLogger(__name__)
_URL = "https://api.idus.com/v3/product/info?uuid={}"
_ITEM_LINK = "https://www.idus.com/v2/product/{}"


class IdusEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        self.id = IdusEngine.parse_id(item_url)
        self.product_id = self.id

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(verify_ssl=False)
            ) as session:
                async with session.get(
                        url=_URL.format(self.product_id),
                        headers={**default_request_headers()},
                ) as response:
                    result = await response.read()

                    if response.status == 200:
                        j = json.loads(result)
                        d = j["items"]

                        _LOGGER.debug("Backpackr Idus Response", d)

                        if d["p_info"]["pi_itemcount"] == -1:
                            inventory = InventoryStatus.IN_STOCK
                        elif d["p_info"]["pi_itemcount"] == 0:
                            inventory = InventoryStatus.OUT_OF_STOCK
                        else:
                            inventory = InventoryStatus.ALMOST_SOLD_OUT

                        return ItemData(
                            id=d["uuid"],
                            name=d["p_info"]["pi_name"],
                            price=float(d["p_info"]["pi_saleprice"].replace(",", "")),
                            category=d["category_name"],
                            description=d["p_keywords"],
                            delivery=DeliveryData(price=0.0),
                            url=_ITEM_LINK.format(d["uuid"]),
                            image=d["p_images"]["pp_mainimage"]["ppi_origin"][
                                "picPath"
                            ],
                            unit=ItemUnitData(
                                price=float(
                                    d["p_info"]["pi_saleprice"].replace(",", "")
                                )
                            ),
                            inventory=inventory,
                        )
                    else:
                        _LOGGER.error("Backpackr Idus Response Error", response)

        except Exception as e:
            _LOGGER.exception("Backpackr Idus Request Error %s", e)

    def id(self) -> str:
        return self.product_id

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"product/(?P<product_id>[\w\d\-]+)", item_url)

        if u is None:
            raise InvalidError('Bad backpackr(idus) item_url "{}".'.format(item_url))

        g = u.groupdict()

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return "idus"

    @staticmethod
    def engine_name() -> str:
        return "Idus"
