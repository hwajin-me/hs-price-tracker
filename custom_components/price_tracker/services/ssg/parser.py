
import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_float, parse_bool, parse_number


class SsgParser:

    _data: dict
    _item: dict
    def __init__(self, response: str):
        try:
            j = json.loads(response)

            if Lu.has(j, 'data.item') is False:
                raise DataParseError("No item found in response")

            self._data = j
            self._item = j["data"]["item"]
        except Exception as e:
            raise DataParseError("Failed to parse response") from e

    @property
    def price(self):
        price = parse_float(Lu.get_or_default(self._item, 'price.sellprc', 0))
        best_price = parse_float(Lu.get_or_default(self._item, 'price.bestprc', price))
        return ItemPriceData(
            original_price=price,
            price=best_price,
            currency='KRW'
        )

    @property
    def inventory_status(self):
        return InventoryStatus.of(parse_bool(self._item["itemBuyInfo"]["soldOut"]),
                                  parse_number(Lu.get(self._item, 'usablInvQty')))

    @staticmethod
    def parse_data(response):
        json_data = json.loads(response)

        if Lu.has(json_data, 'data.item') is False:
            raise DataParseError("No item found in response")

        return json_data["data"]["item"]

    @staticmethod
    def parse_price(response):
        data = SsgParser.parse_data(response)
        if Lu.has(data, 'price.sellprc') is False:
            raise DataParseError("No price found in response")

        price = Lu.get_or_default(data, 'price.sellprc', 0)
        best_price = Lu.get_or_default(data, 'price.bestprc', price)
        return ItemPriceData(
            original_price=price,
            price=best_price,
            currency='KRW'
        )
