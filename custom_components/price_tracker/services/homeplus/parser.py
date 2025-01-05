import json
import logging

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryPayType,
    DeliveryType,
    DeliveryData,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemOptionData
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_bool, parse_number


_LOGGER = logging.getLogger(__name__)


class HomeplusParser:
    """Parser class for Homeplus"""

    def __init__(self, html: str):
        self._html = html
        self._soup = BeautifulSoup(html, "html.parser")
        self._json_raw = self._soup.find("script", {"id": "/item/getItemDetail.json"})
        if self._json_raw:
            try:
                self._json = json.loads(self._json_raw.get_text())
                self._data = self._json["data"]["item"]
                self._basic = self._data["basic"]
                self._sale = self._data["sale"]
                self._options = self._data["opt"]
                self._delivery = self._data["ship"]
                self._etc = self._data["etc"]
                self._images = self._data["img"]
            except Exception as e:
                raise DataParseError("Failed to parse JSON data Homeplus") from e
        else:
            raise DataParseError("Failed to find JSON data Homeplus")

    @property
    def brand(self) -> str:
        return self._basic["storeKind"]

    @property
    def name(self):
        return self._basic["itemNm"]

    @property
    def price(self):
        if self._sale["dcPrice"] == 0:
            return ItemPriceData(
                original_price=self._sale["salePrice"] * self._sale["purchaseMinQty"],
                price=self._sale["salePrice"] * self._sale["purchaseMinQty"],
            )

        return ItemPriceData(
            original_price=self._sale["salePrice"] * self._sale["purchaseMinQty"],
            price=self._sale["dcPrice"] * self._sale["purchaseMinQty"],
        )

    @property
    def description(self):
        return ""

    @property
    def category(self):
        return ItemCategoryData(
            [
                self._basic["lcateNm"],
                self._basic["mcateNm"],
                self._basic["scateNm"],
                self._basic["dcateNm"],
            ]
        )

    @property
    def delivery(self):
        delivery_type = DeliveryType.EXPRESS
        if self._delivery["shipKind"] == "COND":
            pay_type = DeliveryPayType.FREE_OR_PAID
            price = self._delivery["shipFee"]
            free = self._delivery["freeCondition"]

            return DeliveryData(
                pay_type=pay_type,
                price=price,
                threshold_price=free,
                delivery_type=delivery_type,
            )

        return DeliveryData(delivery_type=DeliveryType.STANDARD)

    @property
    def unit(self):
        unit_price = self._etc["unitPrice"]
        unit = ItemUnitType.of(self._etc["unitMeasure"])
        per = self._etc["unitQty"]

        return ItemUnitData(
            price=unit_price, unit_type=unit, unit=per, total_price=self.price.price
        )

    @property
    def inventory_status(self):
        return InventoryStatus.of(
            is_sold_out=parse_bool(self._sale["itemSoldOutYn"]),
            stock=self._sale["stockQty"],
        )

    @property
    def image(self):
        return "https://image.homeplus.kr{}".format(self._images["mainList"][0]["url"])

    @property
    def options(self):
        if self._options is None or len(self._options["optSelList"]) == 0:
            return []

        return Lu.map(
            self._options["optSelList"],
            lambda x: ItemOptionData(
                id=x["optNo"],
                name=x["opt1Val"],
                price=parse_number(x["salePrice"]),
                inventory=x["stockQty"],
            ),
        )
