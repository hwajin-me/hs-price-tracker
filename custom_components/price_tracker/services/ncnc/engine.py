import json
import logging
from datetime import datetime

import aiohttp

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.ncnc.const import CODE, NAME
from custom_components.price_tracker.services.ncnc.parser import NcncParser
from custom_components.price_tracker.utilities.request import default_request_headers

_LOGGER = logging.getLogger(__name__)
_URL = "https://qn9ovn2pnk.execute-api.ap-northeast-2.amazonaws.com/pro/items/v2/{}"
_UA = "NcncNative/605006 CFNetwork/1568.100.1 Darwin/24.0.0"
_X_API = "D3aDpWlEkz7dAp5o2Ew8zZbc4N9mnyK9JFCHgy30"


class NcncEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = NcncEngine.parse_id(item_url)
        self.id = id["product_id"]

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=False)
            ) as session:
                async with session.get(
                    url=_URL.format(self.id),
                    headers={
                        **default_request_headers(),
                        "User-Agent": _UA,
                        "x-api-key": _X_API,
                    },
                ) as response:
                    result = await response.text()

                    if response.status == 200:
                        ncnc_parser = NcncParser(text=result)
                        j = json.loads(result)
                        _LOGGER.debug(
                            "NCNC Fetched at {} - {}", datetime.now(), self.id
                        )

                        d = j["item"]

                        # TODO : Find real item

                        return ItemData(
                            id=d["id"],
                            name=d["name"],
                            price=ncnc_parser.price,
                            description=d["conItems"][0]["info"]
                            if len(d["conItems"])
                            else "",
                            image=d["imageUrl"],
                            category="{}>{}".format(
                                d["conCategory2"]["conCategory1"]["name"],
                                d["conCategory2"]["name"],
                            ),
                            inventory=InventoryStatus.OUT_OF_STOCK
                            if d["isSoldOut"]
                            else InventoryStatus.IN_STOCK,
                            # NO-DELIVERY ITEM(digital)
                        )
                    else:
                        _LOGGER.error("NCNC Response Error", response)

        except Exception:
            _LOGGER.exception("NCNC Request Error")

    def id(self) -> str:
        return self.id

    @staticmethod
    def parse_id(item_url: str):
        return {"product_id": item_url}

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
