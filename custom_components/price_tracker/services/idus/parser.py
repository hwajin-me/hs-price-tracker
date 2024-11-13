import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import DeliveryData, DeliveryPayType
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData
from custom_components.price_tracker.utilities.parser import parse_float


class IdusParser:
    _data: dict

    def __init__(self, text: str):
        try:
            parse = json.loads(text)
            self._data = parse["items"]
        except Exception as e:
            raise DataParseError("Idus Parser Error") from e

    @property
    def name(self):
        return self._data["p_info"]["pi_name"]

    @property
    def brand(self):
        return self._data["artistname"]

    @property
    def description(self):
        return ""

    @property
    def unit(self):
        return ItemUnitData(price=self.price.price)

    @property
    def image(self):
        return self._data["p_images"]["pp_mainimage"]["ppi_origin"]["picPath"]

    @property
    def category(self):
        return ItemCategoryData(self._data["category_name"])

    @property
    def delivery(self):
        return DeliveryData(
            pay_type=DeliveryPayType.FREE, price=0.0, threshold_price=10000
        )

    @property
    def options(self):
        return []

    @property
    def url(self):
        return f"https://www.idus.com/v2/product/{self._data['uuid']}"

    @property
    def inventory_status(self):
        if self._data["p_info"]["pi_itemcount"] == -1:
            inventory = InventoryStatus.IN_STOCK
        elif self._data["p_info"]["pi_itemcount"] == 0:
            inventory = InventoryStatus.OUT_OF_STOCK
        else:
            inventory = InventoryStatus.ALMOST_SOLD_OUT

        return inventory

    @property
    def price(self):
        original_price = parse_float(self._data["p_info"]["pi_price"])
        sale_price = parse_float(self._data["p_info"]["pi_saleprice"])

        return ItemPriceData(price=sale_price, original_price=original_price)
