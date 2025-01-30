import datetime
import json
import re

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryPayType,
    DeliveryType,
    DeliveryData,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemOptionData
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_float


class KurlyParser:
    _data: dict

    def __init__(self, text: str):
        try:
            parse = json.loads(text)
            self._data = parse["data"]
        except Exception as e:
            raise DataParseError("Failed to parse data") from e

    @property
    def id(self):
        return self._data["no"]

    @property
    def brand(self):
        brand_data = Lu.find(self._data["seller_profile"], "title", "판매자")
        if brand_data is None:
            return None

        return brand_data["description"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def image(self):
        return self._data["main_image_url"]

    @property
    def description(self):
        return self._data["short_description"]

    @property
    def category(self):
        return ItemCategoryData(self._data["category_ids"])

    @property
    def delivery(self):
        types = Lu.map(
            self._data["delivery_type_infos"], lambda x: x["type"]
        )  # DAWN, NORMAL_PARCEL, INSTALLATION_DELIVERY
        if "DAWN" in types:
            delivery_price = 3000
            threshold_price = 40000
            pay_type = DeliveryPayType.FREE_OR_PAID
            arrival = (
                datetime.date.today() + datetime.timedelta(days=1)
                if datetime.datetime.now().hour < 23
                else datetime.date.today() + datetime.timedelta(days=2)
            )
            delivery_type = (
                DeliveryType.EXPRESS_NEXT_DAWN
                if datetime.datetime.now().hour < 23
                else DeliveryType.EXPRESS
            )
        else:
            delivery_price = None
            threshold_price = None
            pay_type = DeliveryPayType.UNKNOWN
            delivery_type = DeliveryType.STANDARD
            arrival = None

        return DeliveryData(
            price=delivery_price,
            threshold_price=threshold_price,
            pay_type=pay_type,
            delivery_type=delivery_type,
            arrive_date=arrival,
        )

    @property
    def url(self):
        return f"https://www.kurly.com/goods/{self.id}"

    @property
    def unit(self):
        data = self._data["volume"]
        if data is None or data == "":
            return ItemUnitData(price=self.price.price)

        parse = re.search(
            r"(?P<unit>[\d,.]+).*?(?P<type>개입|kg|g|KG|Kg|ml|ML|mL|L|l)", data
        )

        if parse is None:
            return ItemUnitData(price=self.price.price)

        group = parse.groupdict()
        if group is None or "unit" not in group or "type" not in group:
            return ItemUnitData(price=self.price.price)

        return ItemUnitData(
            price=self.price.price,
            unit=parse_float(group["unit"]),
            unit_type=ItemUnitType.of(group["type"]),
            total_price=self.price.price,
        )

    @property
    def options(self):
        data = self._data["deal_products"]
        if data is not None and len(data) > 0:
            return Lu.map(
                data,
                lambda x: ItemOptionData(
                    id=x["no"],
                    name=x["name"],
                    price=parse_float(x["base_price"]),
                    inventory=0 if x["is_sold_out"] else 100,
                ),
            )
        else:
            return []

    @property
    def inventory(self):
        sold_out = self._data["is_sold_out"]

        return InventoryStatus.of(sold_out)

    @property
    def price(self):
        sale_price = (
            parse_float(self._data["base_price"])
            if self._data["discounted_price"] is None
            or self._data["discounted_price"] == 0
            else parse_float(self._data["discounted_price"])
        )
        original_price = parse_float(self._data["retail_price"])

        return ItemPriceData(price=sale_price, original_price=original_price)
