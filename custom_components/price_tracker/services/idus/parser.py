import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.parser import parse_float


class IdusParser:
    _data: dict

    def __init__(self, text: str):
        try:
            parse = json.loads(text)
            self._data = parse['items']
        except Exception as e:
            raise DataParseError('Idus Parser Error') from e

    @property
    def price(self):
        sale_price = parse_float(self._data["p_info"]["pi_saleprice"])

        return ItemPriceData(
            price=sale_price
        )
