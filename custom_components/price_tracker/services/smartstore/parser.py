import datetime
import json
import re

from bs4 import BeautifulSoup

from custom_components.price_tracker.components.error import (
    DataParseError,
    NotFoundError,
)
from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import (
    DeliveryType,
    DeliveryData,
    DeliveryPayType,
)
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.item import ItemOptionData
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.utilities.list import Lu


class SmartstoreParser:
    def __init__(self, data: str):
        self._html = data
        self._data = None
        try:
            soup = BeautifulSoup(self._html, "html.parser")
            scripts = soup.find_all("script")
            for script in scripts:
                if "window.__PRELOADED_STATE__" in script.text:
                    data = re.search(
                        r"window.__PRELOADED_STATE__=(?P<json>.*)", script.text
                    )
                    self._data = json.loads(data["json"])
                    break

            if self._data is None:
                raise DataParseError(
                    "NAVER Response Error - Data not found (PRELOADED_STATE)"
                )

            if Lu.get(self._data, "product.A.id") is None or Lu.get(
                self._data, "product.A.errorView", False
            ):
                raise NotFoundError("NAVER Response Error - Not found.")

            # For NAVER Shopping
            if Lu.has(self._data, "product.A") is False:
                self._data["product"] = {
                    "A": self._data["productDetail"]["A"]["contents"]
                }
        except NotFoundError as e:
            raise e
        except Exception as e:
            raise DataParseError("NAVER Response Parse Error - Unknown") from e

    @property
    def brand(self):
        return Lu.get(
            self._data["product"]["A"]["naverShoppingSearchInfo"], "brandName"
        )

    @property
    def category(self):
        return ItemCategoryData(
            self._data["product"]["A"]["category"]["wholeCategoryName"]
        )

    @property
    def description(self):
        return Lu.get(self._data, "product.A.description.detailContentText")

    @property
    def image(self):
        return self._data["product"]["A"]["representImage"]["url"]

    @property
    def url(self):
        return self._data["product"]["A"]["productUrl"]

    @property
    def name(self):
        return self._data["product"]["A"]["name"]

    @property
    def inventory_status(self):
        return InventoryStatus.of(
            True if Lu.get(self._data, "product.A.stockQuantity", 1) == 0 else False,
            stock=self._data["product"]["A"]["stockQuantity"],
        )

    @property
    def options(self):
        options = []
        if "optionCombinations" in self._data["product"]["A"]:
            for option in self._data["product"]["A"]["optionCombinations"]:
                options.append(
                    ItemOptionData(
                        id=option["id"],
                        name=option["optionName1"],
                        price=option["price"],
                        inventory=option["stockQuantity"],
                    )
                )

        return options

    @property
    def price(self):
        sale_price = self._data["product"]["A"]["discountedSalePrice"]
        original_price = self._data["product"]["A"]["salePrice"]

        # Payback
        benefits = self._data["product"]["A"]["benefitsView"]
        photo_review = (
            benefits["managerPhotoVideoReviewPoint"] + benefits["photoVideoReviewPoint"]
        )
        text_review = benefits["managerTextReviewPoint"] + benefits["textReviewPoint"]
        after_use_photo_review = (
            benefits["managerAfterUsePhotoVideoReviewPoint"]
            + benefits["afterUsePhotoVideoReviewPoint"]
        )
        after_use_text_review = (
            benefits["managerAfterUseTextReviewPoint"]
            + benefits["afterUseTextReviewPoint"]
        )
        membership = benefits["managerPurchasePoint"] * 2

        return ItemPriceData(
            price=sale_price,
            original_price=original_price,
            payback_price=photo_review
            + text_review
            + after_use_photo_review
            + after_use_text_review
            + membership,
            currency="KRW",
        )

    @property
    def delivery(self):
        delivery_info = self._data["product"]["A"]["productDeliveryInfo"]
        base_fee = Lu.get(delivery_info, "baseFee")
        pay_type = delivery_info["deliveryFeeType"]
        free_price = Lu.get(delivery_info, "freeConditionalAmount")
        lead_time = Lu.get_or_default(
            self._data,
            "product.A.productDailyDeliveryLeadTimes.leadTimeViewType",
            "NORMAL_DELIVERY",
        )

        # Check type and average delivery time
        delivery_avg_time = self._data["product"]["A"]["averageDeliveryLeadTime"][
            "sellerAverageDeliveryLeadTime"
        ]
        if delivery_avg_time < 2:
            delivery_type = DeliveryType.EXPRESS
        elif delivery_avg_time > 3:
            delivery_type = DeliveryType.SLOW
        else:
            delivery_type = DeliveryType.STANDARD

        if "todayDispatch" in self._data["product"]["A"]:
            today_dispatch = self._data["product"]["A"]["todayDispatch"]
            possible_dispatch = Lu.get_or_default(
                today_dispatch, "possibleDispatch", []
            )
            if len(possible_dispatch) > 0:
                date = datetime.datetime.strptime(possible_dispatch[0], "%Y%m%d")
            else:
                date = None
            delivery_type = DeliveryType.STANDARD
        else:
            date = None

        if lead_time == "OVERSEAS_OR_CUSTOMMADE":
            delivery_type = DeliveryType.SLOW

        return DeliveryData(
            price=base_fee,
            threshold_price=free_price,
            delivery_type=delivery_type,
            pay_type=DeliveryPayType.FREE
            if pay_type == "FREE"
            else DeliveryPayType.PAID
            if free_price is None
            else DeliveryPayType.FREE_OR_PAID,
            arrive_date=date,
        )
