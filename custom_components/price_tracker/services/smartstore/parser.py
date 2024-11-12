import json
import re

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData


class SmartstoreParser:
    _html: str
    _data: dict

    def __init__(self, data: str):
        self._html = data
        try:
            soup = BeautifulSoup(self._html, "html.parser")
            scripts = soup.find_all("script")
            for script in scripts:
                if "window.__PRELOADED_STATE__" in script.text:
                    data = re.search(
                        r"window.__PRELOADED_STATE__=(?P<json>.*)", script.text
                    )
                    self._data = json.loads(data['json'])
                    break

            if self._data is None:
                raise DataParseError('Data not found')
        except Exception as e:
            raise DataParseError(str(e))

    @property
    def inventory_status(self):
        return InventoryStatus.of(False, stock=self._data["product"]["A"]["stockQuantity"])

    @property
    def price(self):
        sale_price = self._data["product"]["A"]["discountedSalePrice"]

        return ItemPriceData(
            price=sale_price
        )
