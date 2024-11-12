import json
import logging
import re

import aiohttp

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError, ApiError
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.services.ssg.const import CODE, NAME
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_number, parse_bool
from custom_components.price_tracker.utilities.request import default_request_headers

_LOGGER = logging.getLogger(__name__)

_URL = "https://m.apps.ssg.com/appApi/itemView.ssg"
_ITEM_LINK = "https://emart.ssg.com/item/itemView.ssg?itemId={}&siteNo={}"


class SsgEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        self.id = SsgEngine.parse_id(item_url)
        self.product_id = self.id["product_id"]
        self.site_no = self.id["site_no"]

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(verify_ssl=False)
            ) as session:
                async with session.post(
                        url=_URL,
                        json={
                            "params": {
                                "dispSiteNo": str(self.site_no),
                                "itemId": str(self.product_id),
                            }
                        },
                        headers={
                            **default_request_headers(),
                            "Content-Type": "application/json",
                        },
                ) as response:
                    result = await response.text()

                    if response.status == 200:
                        j = json.loads(result)

                        _LOGGER.debug("SSG Response", j)

                        d = j["data"]["item"]

                        if "sellUnitPrc" in d["price"]:
                            unit_data = re.search(
                                r"^(?P<unit>[\d,]+)(?P<type>\w+) 당 : (?P<price>[\d,]+)원$",
                                d["price"]["sellUnitPrc"],
                            )

                            if unit_data is not None:
                                unitParse = unit_data.groupdict()
                                unit = ItemUnitData(
                                    price=parse_number(unitParse["price"]),
                                    unit_type=ItemUnitType.of(unitParse["type"]),
                                    unit=parse_number(unitParse["unit"]),
                                )
                            else:
                                unit = ItemUnitData(float(d["price"]["sellprc"]))
                        else:
                            unit = ItemUnitData(float(d["price"]["sellprc"]))

                        return ItemData(
                            id=self.product_id,
                            brand=d['brand']['brandNm'] if 'brand' in d else None,
                            name=d["itemNm"],
                            price=parse_number(d["price"]["sellprc"]),
                            description="",
                            url=_ITEM_LINK.format(self.product_id, self.site_no),
                            image=d["uitemImgList"][0]["imgUrl"]
                            if len(d["uitemImgList"]) > 0
                            else None,
                            category=d["ctgNm"],
                            inventory=InventoryStatus.of(parse_bool(d["itemBuyInfo"]["soldOut"]),
                                                         Lu.get(d, 'usablInvQty')),
                            unit=unit,
                        )
                    else:
                        _LOGGER.error("SSG Response Error", response)
        except ApiError as e:
            _LOGGER.exception("SSG Error %s", e)
        except Exception as e:
            _LOGGER.exception("SSG Unknown Error %s", e)

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
