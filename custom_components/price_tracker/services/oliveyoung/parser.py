import json

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryType,
    DeliveryData,
    DeliveryPayType,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemOptionData
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_number, parse_bool


class OliveyoungParser:
    _data: dict = {}

    def __init__(self, text: str):
        try:
            soup = BeautifulSoup(text, "html.parser")
            data = soup.find("textarea", {"id": "goodsData"}).get_text()
            if data is not None:
                self._data = json.loads(data)
            else:
                raise DataParseError("Data not found")
        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError(str(e)) from e

    @property
    def brand(self):
        return self._data["brandName"]

    @property
    def name(self):
        return self._data["goodsBaseInfo"]["goodsName"]

    @property
    def category(self):
        return ItemCategoryData(
            self._data["displayCategoryInfo"]["displayCategoryFullPath"]
        )

    @property
    def description(self):
        return ""

    @property
    def image(self):
        return (
            f"https://image.oliveyoung.co.kr/cfimages/cf-goods/uploads/images/thumbnails/{self._data['images'][0]}"
            if self._data["images"]
            else None
        )

    @property
    def unit(self):
        unit_price_info = self._data["goodsUnitPriceInfo"]
        if unit_price_info["unitPrice"] == 0:
            return ItemUnitData(price=self.price.price, unit_type=ItemUnitType.PIECE)
        else:
            return ItemUnitData(price=self.price.price, unit_type=ItemUnitType.PIECE)

    @property
    def price(self):
        sale_price = parse_number(self._data["finalPrice"])
        supply_price = parse_number(self._data["supplyPrice"])

        return ItemPriceData(price=sale_price, original_price=supply_price)

    @property
    def delivery(self):
        # todayDeliveryFlag
        if self._data["todayDeliveryFlag"]:
            if self._data["optionInfo"]["todayDeliveryAvailableFlag"]:
                delivery_type = DeliveryType.EXPRESS_TODAY
            else:
                delivery_type = DeliveryType.EXPRESS_NEXT_DAY
        else:
            delivery_type = DeliveryType.STANDARD

        if parse_bool(self._data["goodsBaseInfo"]["deliveryFreeFlag"]):
            delivery_pay_type = DeliveryPayType.FREE
        else:
            delivery_pay_type = DeliveryPayType.PAID

        return DeliveryData(
            pay_type=delivery_pay_type,
            delivery_type=delivery_type,
        )

    @property
    def options(self):
        options = self._data["optionInfo"]["optionList"]
        return Lu.map(
            options,
            lambda x: ItemOptionData(
                id=f'{x["goodsNumber"]}_{x["itemNumber"]}',
                price=x["salePrice"],
                name=x["itemName"],
                inventory=x["quantity"],
            ),
        )

    @property
    def inventory_status(self):
        sum_options = sum(
            [x["quantity"] for x in self._data["optionInfo"]["optionList"]]
        )

        return InventoryStatus.of(
            is_sold_out=self._data["optionInfo"]["allSoldoutFlag"], stock=sum_options
        )
