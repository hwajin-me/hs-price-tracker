
import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.list import Lu


class SsgParser:

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
