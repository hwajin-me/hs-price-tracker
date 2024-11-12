import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.parser import parse_float


class NcncParser:
    _data: dict = {}

    def __init__(self, text: str):
        try:
            parse = json.loads(text)
            self._data = parse["item"]
        except Exception as e:
            raise DataParseError('NcncParser Error') from e

    @property
    def price(self):
        sale_price = parse_float(
            self._data["conItems"][0]["minSellingPrice"] if len(self._data["conItems"]) and self._data["conItems"][0]
            else self._data["originalPrice"])

        return ItemPriceData(
            price=sale_price
        )
