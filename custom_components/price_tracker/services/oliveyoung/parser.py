import json

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.parser import parse_number


class OliveyoungParser:
    _data: dict = {}

    def __init__(self, text: str):
        try:
            soup = BeautifulSoup(text, "html.parser")
            data = soup.find("textarea", {"id": "goodsData"}).get_text()
            if data is not None:
                self._data = json.loads(data)
            else:
                raise DataParseError('Data not found')
        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError(str(e)) from e

    @property
    def price(self):
        sale_price = parse_number(self._data['finalPrice'])
        return ItemPriceData(
            price=sale_price
        )
