import json
import re

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryPayType,
    DeliveryType,
    DeliveryData,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_float


class CoupangParser:
    _data: dict
    _page_atf: dict

    def __init__(self, text: str):
        try:
            soup = BeautifulSoup(text, "html.parser")
            if soup is not None:
                data = soup.find("script", {"id": "__NEXT_DATA__"}).get_text()
                j = json.loads(data)
                self._data = j
                page_atf = Lu.find_item(
                    j["props"]["pageProps"]["pageList"], "page", "PAGE_ATF"
                )
                if page_atf is None:
                    raise DataParseError(
                        "Coupang Parse Error (No ATF) - {}".format(
                            j["props"]["pageProps"]["pageList"]
                        )
                    )

                self._page_atf = page_atf["widgetList"]
            else:
                raise DataParseError("Coupang Parser Error (Empty HTML PARSER)")
        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError("Coupang Parser Error") from e

    @property
    def name(self):
        return Lu.find_item(
            self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_PRODUCT_INFO"
        )["data"]["title"]

    @property
    def description(self):
        return ""

    @property
    def brand(self):
        return Lu.get(self._data, "props.pageProps.seoLdJson.brand.name")

    @property
    def category(self):
        return ItemCategoryData(
            list(
                str(t["name"])
                for t in Lu.find_item(
                    self._page_atf,
                    "viewType",
                    "MWEB_PRODUCT_DETAIL_SDP_BREADCURMB_DETAIL",
                )["data"]["breadcrumb"]
                if t["linkcode"] != "0"
            )
        )

    @property
    def options(self):
        return None

    @property
    def price(self):
        price = Lu.find_item(
            self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO"
        )

        if price is None:
            raise DataParseError(
                "Coupang Parse Error - MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO not found"
            )

        price_data = price["data"]
        original_price = (
            price_data["originalPrice"]["price"]
            if Lu.has(price_data, "originalPrice.price")
            else None
        )
        currency = "KRW"
        price = price_data["finalPrice"]["price"]
        payback_price = 0

        return ItemPriceData(
            original_price=original_price,
            price=price,
            currency=currency,
            payback_price=payback_price,
        )

    @property
    def unit(self):
        price_info = Lu.find_item(
            self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO"
        )["data"]

        if "unitPriceDescription" in price_info["finalPrice"]:
            u = re.match(
                r"^\((?P<per>[\d,]+)(?P<unit_type>g|개|ml|kg|l)당 (?P<price>[\d,]+)원\)$",
                price_info["finalPrice"]["unitPriceDescription"],
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
        else:
            unit_price = ItemUnitData(price=self.price.price)

        return unit_price

    @property
    def image(self):
        return Lu.find_item(
            self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_ITEM_THUMBNAILS"
        )["data"]["medias"][0]["detail"]

    @property
    def delivery(self):
        price_info = Lu.find_item(
            self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO"
        )["data"]
        delivery_price = (
            price_info["deliveryMessages"] if "deliveryMessage" in price_info else None
        )
        threshold_price = None
        delivery_pay_type = DeliveryPayType.PAID
        delivery_type = DeliveryType.STANDARD
        if delivery_price is not None:
            delivery_price = parse_float(
                delivery_price.replace("배송비", "")
                .replace("원", "")
                .replace(",", "")
                .replace(" ", "")
            )
        else:
            delivery_price = 0.0
            delivery_pay_type = DeliveryPayType.FREE

        # Find delivery info
        delivery_info_base = Lu.find_item(
            self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_DELIVERY_INFO"
        )
        if (
                delivery_info_base is not None
                and "data" in delivery_info_base
                and "pddList" in delivery_info_base["data"]
                and len(delivery_info_base["data"]["pddList"]) > 0
        ):
            delivery_item = delivery_info_base["data"]["pddList"][0]
            type = delivery_item[
                "deliveryType"
            ]  # ROCKET_MERCHANT , ROCKET, ROCKET_FRESH
            arrival = str(delivery_item.get("arrivalMessage"))

            if arrival is None:
                arrival = ""

            # deliveryMessages
            delivery_pay_type = DeliveryPayType.FREE

            if arrival.find("오늘") > -1:
                if arrival.find("새벽") > -1:
                    delivery_type = DeliveryType.EXPRESS_TODAY_DAWN
                elif arrival.find("오후") > -1:
                    delivery_type = DeliveryType.EXPRESS_TONIGHT
                else:
                    delivery_type = DeliveryType.EXPRESS_TODAY
            elif arrival.find("내일") > -1:
                if arrival.find("새벽") > -1:
                    delivery_type = DeliveryType.EXPRESS_NEXT_DAWN
                elif arrival.find("오후") > -1:
                    delivery_type = DeliveryType.EXPRESS_NEXT_DAY
                else:
                    delivery_type = DeliveryType.EXPRESS_NEXT_DAY
            else:
                if type in ["ROCKET", "ROCKET_FRESH", "ROCKET_MERCHANT"]:
                    delivery_type = DeliveryType.EXPRESS
                else:
                    delivery_type = DeliveryType.STANDARD

            if type == "ROCKET_FRESH":
                threshold_price = 15000
            else:
                threshold_price = None

        return DeliveryData(
            price=delivery_price,
            pay_type=delivery_pay_type,
            delivery_type=delivery_type,
            threshold_price=threshold_price,
        )

    @property
    def inventory(self):
        inventory = (
            Lu.find_item(
                self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_ATF_QUANTITY"
            )["data"]
            if Lu.find_item(
                self._page_atf, "viewType", "MWEB_PRODUCT_DETAIL_ATF_QUANTITY"
            )
               is not None
            else None
        )

        sold_out = self._data["props"]["pageProps"]["properties"]["itemDetail"][
            "soldOut"
        ]

        if (inventory is None or "limitMessage" not in inventory) and not sold_out:
            stock = InventoryStatus.IN_STOCK
        elif not sold_out and "limitMessage" in inventory:
            stock = InventoryStatus.ALMOST_SOLD_OUT
        elif not sold_out:
            stock = InventoryStatus.IN_STOCK
        else:
            stock = InventoryStatus.OUT_OF_STOCK

        return stock
