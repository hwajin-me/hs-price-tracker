import datetime
import json
import logging
import re

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.delivery import (
    DeliveryPayType,
    DeliveryType,
    DeliveryData,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_number

_LOGGER = logging.getLogger(__name__)


class CoupangParser:
    _data: dict
    _base: dict
    _page_atf: dict
    _media: dict

    def __init__(self, text: str):
        try:
            data = json.loads(text)

            if "rCode" not in data or data["rCode"] != "RET0000":
                raise DataParseError(
                    "Coupang Parse Error (rCode) - {}".format(data["rCode"])
                )
            self._page_atf = Lu.get(
                Lu.find(Lu.get(data, "rData.pageList"), "page", "PAGE_ATF"),
                "widgetList",
                [],
            )
            self._base = Lu.get(
                Lu.find(
                    Lu.get(data, "rData.pageList"),
                    "page",
                    "PAGE_HANDLEBAR",
                    Lu.find(
                        Lu.get(data, "rData.pageList"),
                        "page",
                        "PAGE_FASHION_HANDLEBAR",
                        {},
                    ),
                ),
                "widgetList",
                [],
            )
            self._media = Lu.get(
                Lu.find(
                    self._page_atf,
                    "entity.viewType",
                    "PRODUCT_DETAIL_ITEM_THUMBNAILS",
                    {},
                ),
                "entity.medias.0.detail",
                [],
            )
            self._data = {}

            delivery = "".join(
                Lu.map(
                    Lu.get(
                        Lu.find(
                            self._base,
                            "entity.viewType",
                            "PRODUCT_DETAIL_HANDLEBAR_QUANTITY",
                        ),
                        "entity.deliveryDate",
                        [],
                    ),
                    lambda x: x["text"],
                )
            )
            delivery_price = "".join(
                Lu.map(
                    Lu.get(
                        Lu.find(
                            self._base,
                            "entity.viewType",
                            "PRODUCT_DETAIL_BASE_INFO",
                            {},
                        ),
                        "entity.deliveryInfo.shippingFee",
                        [],
                    ),
                    lambda x: x["text"] if x is not None else "",
                )
            )

            if delivery is not None and delivery != "":
                self._data = {**self._data, "deliveryMessage": delivery}

            if delivery_price is not None and delivery_price != "":
                self._data = {**self._data, "deliveryFee": delivery_price}

            if self._media is not None:
                self._data = {**self._data, "image": self._media}
            self._data = {
                **self._data,
                **{
                    "finalPrice": Lu.get(
                        Lu.find(
                            self._base,
                            "entity.viewType",
                            "PRODUCT_DETAIL_BASE_INFO",
                            {},
                        ),
                        "priceInfo.finalPrice.0",
                        Lu.get(self._data, "finalPrice"),
                    )
                },
                **{
                    "originalPrice": Lu.get(
                        Lu.find(
                            self._base,
                            "entity.viewType",
                            "PRODUCT_DETAIL_BASE_INFO",
                            {},
                        ),
                        "priceInfo.originalPrice.0",
                        Lu.get(self._data, "originalPrice"),
                    )
                },
            }
            self._data = {
                **self._data,
                **Lu.get(
                    data,
                    "rData.properties.pageSession.logging.exposureSchema.mandatory",
                    {},
                ),
                **Lu.get(
                    data,
                    "rData.properties.pageSession.logging.bypass.exposureSchema.mandatory",
                    {},
                ),
                **Lu.get(
                    data,
                    "rData.properties.itemDetail.logging.exposureSchema.mandatory",
                    {},
                ),
                **Lu.get(
                    data,
                    "rData.properties.itemDetail.logging.bypass.exposureSchema.mandatory",
                    {},
                ),
                **Lu.get(
                    data,
                    "rData.properties.itemDetail.handleBarLogging.bypass.exposureSchema.mandatory",
                    {},
                ),
            }

        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError("Coupang Parser Error") from e

    @property
    def name(self):
        return Lu.get(
            Lu.find(self._page_atf, "entity.viewType", "PRODUCT_DETAIL_PRODUCT_INFO"),
            "entity.title.0.text",
            "Unknown (Coupang)",
        )

    @property
    def description(self):
        return ""

    @property
    def brand(self):
        return Lu.get(self._data, "brandName")

    @property
    def category(self):
        return None

    @property
    def options(self):
        return None

    @property
    def price(self):
        return ItemPriceData(
            original_price=Lu.get(self._data, "originalPrice"),
            price=Lu.get(self._data, "finalPrice"),
            currency="KRW",
            payback_price=0,
        )

    @property
    def unit(self):
        price_info = Lu.get(self._data, "unitPrice")
        if price_info is None:
            return ItemUnitData(price=self.price.price)

        u = re.match(
            r"^\((?P<per>[\d,]+)(?P<unit_type>g|개|ml|kg|l)당 (?P<price>[\d,]+)원\)$",
            price_info,
        )
        if u is None:
            return ItemUnitData(price=self.price.price)
        g = u.groupdict()
        unit_price = ItemUnitData(
            unit_type=ItemUnitType.of(g["unit_type"]),
            unit=float(g["per"].replace(",", "")),
            price=float(g["price"].replace(",", "")),
            total_price=self.price.price,
        )

        return unit_price

    @property
    def image(self):
        return Lu.get(self._data, "image", None)

    @property
    def delivery(self):
        rocket_type = Lu.get(self._data, "rocketType", "STANDARD")
        delivery_message = Lu.get(
            str(Lu.get(self._data, "deliveryMessage", "")).split("\n"), 0
        )
        delivery_fee = parse_number(
            str(Lu.get(self._data, "deliveryFee", "free"))
            .replace("배송비", "")
            .replace("원", "")
            .replace(",", "")
            .replace(" ", "")
        )
        threshold_price = None
        arrival_date = None

        if rocket_type == "ROCKET":
            delivery_type = DeliveryType.EXPRESS
        elif rocket_type == "ROCKET_FRESH":
            delivery_type = DeliveryType.EXPRESS
            threshold_price = 15000
        elif rocket_type == "ROCKET_MERCHANT" or rocket_type == "ROCKET_MERCHANT_V3":
            delivery_type = DeliveryType.EXPRESS
        elif rocket_type == "COUPANG_GLOBAL":
            delivery_type = DeliveryType.SLOW
        else:
            delivery_type = DeliveryType.STANDARD

        if delivery_fee == 0:
            delivery_pay_type = DeliveryPayType.FREE
        else:
            delivery_pay_type = DeliveryPayType.PAID

        if rocket_type in [
            "ROCKET",
            "ROCKET_FRESH",
            "ROCKET_MERCHANT",
            "ROCKET_MERCHANT_V3",
        ]:
            if delivery_message.find("오늘") > -1:
                if delivery_message.find("새벽") > -1:
                    delivery_type = DeliveryType.EXPRESS_TODAY_DAWN
                elif delivery_message.find("오후") > -1:
                    delivery_type = DeliveryType.EXPRESS_TONIGHT
                else:
                    delivery_type = DeliveryType.EXPRESS_TODAY
            elif delivery_message.find("내일") > -1:
                if delivery_message.find("새벽") > -1:
                    delivery_type = DeliveryType.EXPRESS_NEXT_DAWN
                elif delivery_message.find("오후") > -1:
                    delivery_type = DeliveryType.EXPRESS_NEXT_DAY
                else:
                    delivery_type = DeliveryType.EXPRESS_NEXT_DAY
            else:
                delivery_type = DeliveryType.EXPRESS
        else:
            message_parse = re.match(
                r"(?P<weekday>[월화수목금토일])요일 (?P<date>\d{1,2}/\d{1,2})",
                delivery_message,
            )
            if message_parse is not None:
                g = message_parse.groupdict()
                arrival_date = datetime.datetime.strptime(
                    f"{datetime.datetime.now().year}/{g['date']}", "%Y/%m/%d"
                )

        return DeliveryData(
            price=delivery_fee,
            pay_type=delivery_pay_type,
            delivery_type=delivery_type,
            threshold_price=threshold_price,
            arrive_date=arrival_date,
        )

    @property
    def inventory(self):
        almost_oos = Lu.get(self._data, "isAlmostOSS", False)
        is_out_of_stock = Lu.get(self._data, "isOutOfStock", False)

        if is_out_of_stock:
            stock = InventoryStatus.OUT_OF_STOCK
        elif almost_oos:
            stock = InventoryStatus.ALMOST_SOLD_OUT
        else:
            stock = InventoryStatus.IN_STOCK

        return stock
