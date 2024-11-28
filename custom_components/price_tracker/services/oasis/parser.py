import re

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryType,
    DeliveryPayType,
    DeliveryData,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_number


class OasisParser:
    _data: BeautifulSoup

    def __init__(self, text: str):
        try:
            self._data = BeautifulSoup(text, "html.parser")
        except Exception as e:
            raise DataParseError("OASIS Failed to parse data") from e

    @property
    def name(self):
        return (
            self._data.find("div", class_="oDetail_info_group_title")
            .find("h1")
            .get_text()
            .strip()
        )

    @property
    def brand(self):
        target = self._data.find("div", class_="oDetail_info_gr_shopName")
        if target is None:
            return None

        return target.find("strong").get_text().strip()

    @property
    def description(self):
        data = self._data.find("div", "detailView_body")
        if data is None:
            return None

        return data.get_text().strip()

    @property
    def category(self):
        data = self._data.find("div", "o_currentPath")
        if data is None:
            return None

        items = data.find_all("a")
        if items is None:
            return None

        categories = Lu.map(items, lambda x: x.get_text().strip())
        categories = Lu.remove(categories, lambda x: x == "홈")
        categories = Lu.remove(categories, lambda x: x == "추천")

        return ItemCategoryData(categories)

    @property
    def delivery(self):
        info = self._data.find("div", "oDetail_info_group2")
        if info is None:
            return None

        delivery_types = info.find_all("em")
        if "새벽배송" in delivery_types:
            delivery_type = DeliveryType.EXPRESS_NEXT_DAWN
        elif "당일배송" in delivery_types:
            delivery_type = DeliveryType.EXPRESS_TODAY
        elif "택배배송" in delivery_types:
            delivery_type = DeliveryType.STANDARD
        else:
            delivery_type = DeliveryType.STANDARD

        # 산지출고여부
        for s in self._data.find_all("dd", "notice"):
            if s.get_text().strip().startswith("산지출고일: ") is True:
                delivery_type = DeliveryType.EXPRESS

        delivery_save = info.find("dd", "deliverySave")
        delivery_price = None
        threshold_price = None
        if delivery_save is not None:
            delivery_save_data = delivery_save.get_text().strip().replace("\t", "")
            if delivery_save_data == "0원":
                delivery_price_type = DeliveryPayType.FREE
            else:
                split_data = delivery_save_data.split("원 (")
                if len(split_data) != 2:
                    delivery_price_type = DeliveryPayType.UNKNOWN
                else:
                    delivery_price = parse_number(split_data[0])
                    threshold_price = parse_number(
                        split_data[1].replace("원 이상 무료)", "")
                    )
                    delivery_price_type = DeliveryPayType.FREE_OR_PAID
        else:
            delivery_price_type = DeliveryPayType.UNKNOWN

        return DeliveryData(
            price=delivery_price,
            threshold_price=threshold_price,
            pay_type=delivery_price_type,
            delivery_type=delivery_type,
        )

    @property
    def unit(self):
        for detail_data in self._data.find_all("div", class_="oDetail_info_group2"):
            for dd in detail_data.find_all("dd"):
                target_for_unit = dd.get_text().replace("\n", "").replace("\t", "")
                target_unit_regex = re.search(
                    r"(?P<unit>[\d,]+)(?P<type>g|ml|mL|l|L|kg|Kg)당(?: |)(?P<price>[\d,]+)원",
                    target_for_unit,
                )
                if target_unit_regex is not None:
                    g = target_unit_regex.groupdict()
                    return ItemUnitData(
                        price=float(g["price"].replace(",", "")),
                        unit_type=ItemUnitType.of(g["type"]),
                        unit=float(g["unit"].replace(",", "")),
                    )

        return None

    @property
    def image(self):
        return self._data.find("li", class_="swiper-slide").find("img")["src"]

    @property
    def inventory(self):
        for data in self._data.find_all("a", "buyItNowFromDetail"):
            if data.get_text().strip() == "품절":
                return InventoryStatus.OUT_OF_STOCK

        return InventoryStatus.IN_STOCK

    @property
    def price(self):
        sale_price = parse_number(
            self._data.find("div", class_="discountPrice").get_text().replace("원", "")
        )
        original_price = (
            parse_number(
                self._data.find("div", "oDetail_info_group_price")
                .find("div", class_="cost")
                .get_text()
                .replace("원", "")
            )
            if self._data.find("div", "oDetail_info_group_price").find(
                "div", class_="cost"
            )
            is not None
            else None
        )

        return ItemPriceData(price=sale_price, original_price=original_price)

    @property
    def options(self):
        return None
