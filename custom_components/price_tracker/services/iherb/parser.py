import json
import re

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryData,
    DeliveryPayType,
    DeliveryType,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_float


class IherbParser:
    """iHerb parser"""

    def __init__(self, data: str):
        try:
            parse = json.loads(data)
            self._data = parse
        except Exception as e:
            raise DataParseError("iHerb Parser Error") from e

    @property
    def brand(self):
        return self._data.get("brandName")

    @property
    def name(self):
        return self._data.get("displayName")

    @property
    def category(self):
        ranks = self._data.get("productRanks")
        if ranks:
            return ItemCategoryData(
                Lu.map(ranks, lambda x: x.get("categoryDisplayName"))
            )
        return None

    @property
    def description(self):
        description = self._data.get("description")
        if description is None:
            return ""

        remover = re.compile(r"<.*?>")
        return str(re.sub(remover, "", description.replace("\n", " ")))

    @property
    def inventory_status(self):
        return InventoryStatus.of(self._data.get("stockStatusMessage") == "In stock")

    @property
    def options(self):
        return []

    @property
    def price(self):
        original_price = self._data.get("listPriceAmount")
        price = self._data.get("discountPriceAmount")

        return ItemPriceData(
            original_price=original_price,
            price=price,
        )

    @property
    def url(self):
        return self._data.get("url")

    @property
    def status(self):
        return (
            ItemStatus.ACTIVE
            if self._data.get("productStatus") == "0"
            else ItemStatus.INACTIVE
        )

    @property
    def unit(self):
        unit_price = self._data.get("pricePerUnit")
        match = re.search(r"(?P<price>[\d,]+)/", unit_price)
        if match is None or match.group("price") is None:
            return None

        return ItemUnitData(
            unit_type=ItemUnitType.PILL, price=parse_float(match.group("price")), unit=1
        )

    @property
    def delivery(self):
        return DeliveryData(
            price=5000,
            threshold_price=40000,
            pay_type=DeliveryPayType.FREE_OR_PAID,
            delivery_type=DeliveryType.SLOW,
        )

    @property
    def image(self):
        if (
            self._data.get("campaignImages") is not None
            and len(self._data.get("campaignImages")) > 0
        ):
            return self._data.get("campaignImages")[0]
