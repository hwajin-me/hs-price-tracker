from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.parser import parse_number


class OasisParser:
    _data: BeautifulSoup

    def __init__(self, text: str):
        try:
            self._data = BeautifulSoup(text, "html.parser")
        except Exception as e:
            raise DataParseError("Failed to parse data") from e

    @property
    def price(self):
        sale_price = parse_number(
            self._data.find("div", class_="discountPrice").get_text().replace("원", "")
        )

        return ItemPriceData(
            price=sale_price
        )
