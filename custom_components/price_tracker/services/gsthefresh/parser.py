import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.price import ItemPriceData


class GsthefreshParser:

    _data: dict
    _item: dict
    def __init__(self, text: str):
        try:
            parse = json.loads(text)

            if (
                "data" not in parse
                or "weDeliveryItemDetailResultList" not in parse["data"]
                or len(parse["data"]["weDeliveryItemDetailResultList"]) < 1
            ):
                raise DataParseError("GS THE FRESH Response error")

            self._data = parse['data']
            self._item = self._data["weDeliveryItemDetailResultList"][0]
        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError('GS THE FRESH Parser Error') from e

    @property
    def price(self):
        sale_price = self._item["normalSalePrice"] - self._item["totalDiscountRateAmount"]

        return ItemPriceData(
            price=sale_price
        )
