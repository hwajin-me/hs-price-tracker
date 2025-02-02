import json
import re

from custom_components.price_tracker.components.error import (
    DataParseError,
    NotFoundError,
)
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryData,
    DeliveryPayType,
    DeliveryType,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import (
    parse_float,
    parse_bool,
    parse_number,
)


class SsgParser:
    _data: dict
    _item: dict

    def __init__(self, response: str):
        try:
            j = json.loads(response)

            if Lu.get(j, "data.action.type") == "0001":
                raise NotFoundError("SSG Parser Item not found")

            if Lu.has(j, "data.item") is False:
                raise DataParseError("SSG Parser No item found in response")

            self._data = j["data"]
            self._item = j["data"]["item"]
        except NotFoundError as e:
            raise e
        except Exception as e:
            raise DataParseError("Failed to parse response") from e

    @property
    def price(self):
        price = parse_float(Lu.get_or_default(self._item, "price.sellprc", 0))
        best_price = parse_float(Lu.get_or_default(self._item, "price.bestAmt", price))
        return ItemPriceData(original_price=price, price=best_price, currency="KRW")

    @property
    def inventory_status(self):
        return InventoryStatus.of(
            parse_bool(self._item["itemBuyInfo"]["soldOut"]),
            parse_number(Lu.get(self._item, "usablInvQty")),
        )

    @property
    def brand(self):
        return self._item["brand"]["brandNm"] if "brand" in self._item else None

    @property
    def name(self):
        return self._item["itemNm"]

    @property
    def description(self):
        return ""

    @property
    def url(self):
        return f"https://emart.ssg.com/item/itemView.ssg?itemId={self._item['itemId']}&siteNo={self._item['siteNo']}"

    @property
    def image(self):
        if len(self._item["uitemImgList"]) < 1:
            return None

        return self._item["uitemImgList"][0]["imgUrl"]

    @property
    def category(self):
        if Lu.has(self._data, "itemDispCtgList") is False:
            return ItemCategoryData(self._item["ctgNm"])

        return ItemCategoryData(
            Lu.map(self._data["itemDispCtgList"], lambda x: x["dispCtgNm"])
        )

    @property
    def unit(self):
        if "sellUnitPrc" in self._item["price"]:
            unit_data = re.search(
                r"^(?P<unit>[\d,]+)(?P<type>\w+) 당 : (?P<price>[\d,]+)원$",
                self._item["price"]["sellUnitPrc"],
            )

            if unit_data is not None:
                unit_parse = unit_data.groupdict()
                unit = ItemUnitData(
                    price=parse_number(unit_parse["price"]),
                    unit_type=ItemUnitType.of(unit_parse["type"]),
                    unit=parse_number(unit_parse["unit"]),
                    total_price=self.price.price,
                )
            else:
                unit = ItemUnitData(parse_float(self._item["price"]["sellprc"]))
        else:
            unit = ItemUnitData(parse_float(self._item["price"]["sellprc"]))

        return unit

    @property
    def delivery(self):
        if Lu.has(self._item, "rightBadgeList") is True:
            if Lu.find(self._item["rightBadgeList"], "txt", "쓱-배송") is not None:
                return DeliveryData(
                    price=3000,
                    threshold_price=40000,
                    pay_type=DeliveryPayType.FREE_OR_PAID,
                    delivery_type=DeliveryType.EXPRESS_SPECIFIC,
                )
            elif Lu.find(self._item["rightBadgeList"], "txt", "새벽배송") is not None:
                return DeliveryData(
                    price=3000,
                    threshold_price=40000,
                    pay_type=DeliveryPayType.FREE_OR_PAID,
                    delivery_type=DeliveryType.EXPRESS_SPECIFIC_DAWN,
                )

        if Lu.has(self._data, "itemInfo.deliTypeInfo") is True:
            if Lu.has(self._data["itemInfo"]["deliTypeInfo"], "msgMapList") is False:
                return DeliveryData(pay_type=DeliveryPayType.FREE)

            if (
                item := Lu.find_by(
                    self._data["itemInfo"]["deliTypeInfo"]["msgMapList"],
                    "msg",
                    lambda x: str(x).endswith("원 이상 무료)"),
                )
            ) is not None:
                threshold = parse_number(
                    str(item["msg"])
                    .replace("무료 (", "")
                    .replace(" 이상 무료)", "")
                    .replace("만원", "0000")
                    .replace("천원", "000")
                )
                return DeliveryData(
                    threshold_price=threshold, pay_type=DeliveryPayType.FREE_OR_PAID
                )

            if (
                item := Lu.find_by(
                    self._data["itemInfo"]["deliTypeInfo"]["msgMapList"],
                    "msg",
                    lambda x: str(x).startswith("배송비 "),
                )
            ) is not None:
                price = parse_number(str(item["msg"]).replace("배송비 ", ""))
                return DeliveryData(price=price, pay_type=DeliveryPayType.PAID)

            if (
                Lu.find(
                    self._data["itemInfo"]["deliTypeInfo"]["msgMapList"],
                    "msg",
                    "배송비 무료",
                )
                is not None
            ):
                return DeliveryData(pay_type=DeliveryPayType.FREE)

            return DeliveryData(pay_type=DeliveryPayType.PAID)

        return DeliveryData(
            pay_type=DeliveryPayType.FREE_OR_PAID,
        )
