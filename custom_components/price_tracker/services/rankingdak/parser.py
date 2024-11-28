import re
from datetime import datetime

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import DataParseError
from custom_components.price_tracker.datas.delivery import (
    DeliveryData,
    DeliveryPayType,
    DeliveryType,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemOptionData
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.parser import parse_float, parse_number


class RankingdakParser:
    def __init__(self, html: str):
        try:
            soup = BeautifulSoup(html, "html.parser")
            self._html = soup
            self._best_review = self._html.find(
                "form", {"name": "searchBestReviewForm"}
            )
            self._prod_review = self._html.find(
                "form", {"name": "searchProdReviewForm"}
            )
            self._best_review_detail = self._html.find(
                "form", {"name": "bestReviewDetailForm"}
            )
            self._ice_box_review = self._html.find("form", {"name": "iceboxReviewForm"})
            self._product_counsel = self._html.find(
                "form", {"name": "productCounselForm"}
            )
            self._delivery_info = self._html.find(
                "form", {"name": "productDeliveryInfoForm"}
            )
            self._price = self._html.find("div", class_="price-info")
            self._goods_price = self._html.find("div", class_="goods-price")
            self._table_items = self._html.find_all("div", class_="table-item")
            if self._product_counsel is None or self._price is None:
                raise DataParseError("Data not found")
        except DataParseError as e:
            raise e
        except Exception as e:
            raise DataParseError(str(e)) from e

    @property
    def brand(self):
        for table in self._table_items:
            if table.find("em").get_text() == "브랜드관":
                return table.find("a").get_text()

        return None

    @property
    def name(self):
        return self._product_counsel.find("input", {"name": "productnm"}).get("value")

    @property
    def price(self):
        origin_price = parse_float(
            self._goods_price.find("p", class_="origin").get_text().strip()
        )
        sale_price = parse_float(
            self._goods_price.find("p", class_="price").get_text().strip()
        )
        point = self._price.find("span", class_="orderTotalPoint")
        if point is not None:
            point = parse_float(point.get_text())
        else:
            point = 0

        return ItemPriceData(
            original_price=origin_price, price=sale_price, payback_price=point
        )

    @property
    def image(self):
        image_area = self._html.find("div", class_="goods-img-area")
        images = image_area.find_all("img")

        if images is not None and len(images) > 0:
            return images[0].get("src")

        return None

    @property
    def description(self):
        if data := self._html.find("div", class_="ingredient_wrap"):
            return data.get_text()

        return ""

    @property
    def category(self):
        return None

    @property
    def delivery(self):
        for table in self._table_items:
            if table.find("em").get_text() == "배송방법":
                empty_target = table.find("span", class_="blind")
                if (
                        empty_target is not None
                        and empty_target.get_text().strip() == "무료배송"
                ):
                    return DeliveryData(
                        price=0,
                        threshold_price=0,
                        pay_type=DeliveryPayType.FREE,
                        delivery_type=DeliveryType.STANDARD,
                    )

                methods = Lu.map(
                    table.find("span", class_="title-list").get_text().split(","),
                    lambda x: x.strip(),
                )

                if "특급배송" in methods:
                    return DeliveryData(
                        price=4000,
                        threshold_price=80000,
                        pay_type=DeliveryPayType.FREE_OR_PAID,
                        delivery_type=DeliveryType.EXPRESS_TODAY
                        if datetime.now().hour < 11
                        else DeliveryType.EXPRESS_NEXT_DAWN,
                    )

        return DeliveryData(
            price=3000,
            threshold_price=40000,
            pay_type=DeliveryPayType.FREE_OR_PAID,
            delivery_type=DeliveryType.STANDARD,
        )

    @property
    def unit(self):
        detail = self._goods_price.find("p", class_="price-detail")
        if detail is None:
            return ItemUnitData(price=self.price.price, unit=1)
        parse = re.search(
            r"(?P<q>[\d,]+)(?P<type>팩|g|kg)당 : (?P<price>[\d,]+)원", detail.get_text()
        )
        group = parse.groupdict()
        if group is None:
            return ItemUnitData(price=self.price.price, unit=1)

        return ItemUnitData(
            unit=parse_number(group["q"]),
            price=parse_number(group["price"]),
            unit_type=ItemUnitType.of(group["type"]),
            total_price=self.price.price,
        )

    @property
    def options(self):
        list = self._html.find("ul", class_="selected-options-ul1")
        if list is None:
            return None
        items = list.find_all("li")
        return Lu.map(
            items,
            lambda x: ItemOptionData(
                id=x.get("data-id"),
                name=x.get("data-name"),
                price=parse_float(x.get("data-amt")),
            ),
        )

    @property
    def inventory_status(self):
        return InventoryStatus.IN_STOCK
