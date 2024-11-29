import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import DeliveryData, DeliveryType
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData


class NcncParser:
    _data: dict = {}
    _item: dict = {}

    def __init__(self, text: str):
        try:
            parse = json.loads(text)
            self._data = parse
            self._item = self._data["item"]
        except Exception as e:
            raise DataParseError("NcncParser Error") from e

    @property
    def id(self):
        return self._item["id"]

    @property
    def brand(self):
        return self._item["conCategory2"]["name"]

    @property
    def description(self):
        for item in self._item["conItems"]:
            if item["isSoldOut"]:
                continue

            return item["info"]

    @property
    def name(self):
        return self._item["name"]

    @property
    def image(self):
        return self._item["imageUrl"]

    @property
    def category(self):
        return ItemCategoryData(
            "{}>{}".format(
                self._item["conCategory2"]["conCategory1"]["name"],
                self._item["conCategory2"]["name"],
            )
        )

    @property
    def price(self):
        for item in self._item["conItems"]:
            if item["isSoldOut"]:
                continue
            price = item["minSellingPrice"]

            return ItemPriceData(
                price=price, original_price=self._item["originalPrice"]
            )

        return ItemPriceData(price=self._item["originalPrice"])

    @property
    def unit(self):
        return ItemUnitData(price=self.price.price)

    @property
    def delivery(self):
        return DeliveryData(delivery_type=DeliveryType.NO_DELIVERY)

    @property
    def inventory_status(self):
        if len(self._item["conItems"]) > 0 and self._item["conItems"][0]["isSoldOut"]:
            if len(self._item["conItems"]) == 1:
                return InventoryStatus.OUT_OF_STOCK

            return InventoryStatus.ALMOST_SOLD_OUT

        for item in self._item["conItems"]:
            if item["isSoldOut"]:
                continue

            return InventoryStatus.IN_STOCK

        return InventoryStatus.OUT_OF_STOCK
