import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryData,
    DeliveryPayType,
    DeliveryType,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData
from custom_components.price_tracker.utilities.parser import parse_bool


class DaisoKrParser:
    def __init__(self, data: str | None):
        """Initialize the parser."""
        if data is None:
            raise DataParseError("Empty data for daiso kr")

        try:
            parse = json.loads(data)
            self._data = parse.get("data")
        except json.JSONDecodeError as e:
            raise DataParseError("Failed to parse data for daiso kr") from e

    @property
    def brand(self):
        return "다이소"

    @property
    def name(self):
        return self._data.get("pdNm")

    @property
    def image(self):
        return "https://cdn.daisomall.co.kr{}".format(self._data.get("imgUrl"))

    @property
    def description(self):
        return ""

    @property
    def inventory_status(self):
        return InventoryStatus.of(is_sold_out=False, stock=self._data.get("stckQy"))

    @property
    def category(self):
        cate = self._data.get("exhCtgr")
        if cate is not None and len(cate) > 0:
            return ItemCategoryData(
                [
                    cate[0].get("lctgrNm"),
                    cate[0].get("mctgrNm"),
                    cate[0].get("sctgrNm"),
                ]
            )

        return None

    @property
    def options(self):
        return []

    @property
    def price(self):
        sale_price = self._data.get("pdPrc")

        return ItemPriceData(price=sale_price)

    @property
    def unit(self):
        return ItemUnitData(price=self.price.price)

    @property
    def delivery(self):
        if parse_bool(self._data.get("dlvcExpectExhYn")):
            return DeliveryData(delivery_type=DeliveryType.PICKUP)

        return DeliveryData(
            price=3000, threshold_price=30000, pay_type=DeliveryPayType.FREE_OR_PAID
        )
