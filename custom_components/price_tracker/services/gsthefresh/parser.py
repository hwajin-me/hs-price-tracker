import json

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.delivery import (
    DeliveryData,
    DeliveryType,
    DeliveryPayType,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_bool, parse_number


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

            self._data = parse["data"]
            self._item = self._data["weDeliveryItemDetailResultList"][0]
        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError("GS THE FRESH Parser Error") from e

    @property
    def name(self):
        return self._item["indicateItemName"]

    @property
    def description(self):
        return self._item["itemNotification"]

    @property
    def inventory_status(self):
        return InventoryStatus.of(
            is_sold_out=parse_bool(self._item["soldOutYn"]),
            stock=self._item["stockQuantity"]
            if "stockQuantity" in self._item
            else None,
        )

    @property
    def category(self):
        return None

    @property
    def brand(self):
        return None

    @property
    def delivery(self):
        delivery_data = self._data["processingDeliveryAmountResultList"]
        if delivery_data is not None and len(delivery_data) > 0:
            delivery_price_comm = Lu.find(delivery_data, "commonCode", 3)
            if delivery_price_comm is not None and delivery_price_comm > 0:
                pay_type = DeliveryPayType.PAID
            else:
                pay_type = DeliveryPayType.FREE
        else:
            pay_type = DeliveryPayType.UNKNOWN

        # 기본은 PICKUP 이고, processingDeliveryAmountResultList 의 우딜 여부 체크
        data = self._data["processingDeliveryAmountResultList"]
        min_price_raw = Lu.find(data, "commonCodeName", "우딜 최소주문금액")
        min_price = min_price_raw["amount"] if min_price_raw is not None else 0
        free_threshold_raw = Lu.find(data, "commonCodeName", "우딜 무료배송기준금액")
        free_threshold = (
            free_threshold_raw["amount"] if free_threshold_raw is not None else None
        )
        delivery_price_raw = Lu.find(data, "commonCodeName", "우딜 배송비금액")
        delivery_price = (
            parse_number(delivery_price_raw["amount"])
            if delivery_price_raw is not None
            else None
        )
        if delivery_price is not None and delivery_price > 0:
            pay_type = DeliveryPayType.PAID
        elif delivery_price is None or delivery_price == 0:
            pay_type = DeliveryPayType.FREE

        return DeliveryData(
            price=delivery_price,
            threshold_price=free_threshold,
            minimum_price=min_price,
            delivery_type=DeliveryType.PICKUP,
            pay_type=pay_type,
        )

    @property
    def unit(self):
        return ItemUnitData(price=self.price.price)

    @property
    def price(self):
        sale_price = (
            self._item["normalSalePrice"] - self._item["totalDiscountRateAmount"]
        )

        return ItemPriceData(
            price=sale_price, original_price=self._item["normalSalePrice"]
        )

    @property
    def image(self):
        return self._item["weDeliveryItemImageUrl"]
