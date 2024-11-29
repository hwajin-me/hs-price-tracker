import datetime
import json

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


class LotteOnParser:
    def __init__(self, data: str, discount: str | None = None):
        try:
            parse = json.loads(data)
            self._data = parse
            self._basic = parse["data"]["basicInfo"]
            self._images = parse["data"]["imgInfo"]
            self._options = parse["data"].get("bundleSellerProductList")
            self._price = parse["data"]["priceInfo"]
            self._stock = parse["data"]["stckInfo"]
            self._delivery = parse["data"]["dlvInfo"]
            self._category = parse["data"]["dispCategoryInfo"]

            if discount:
                self._discount = json.loads(discount)
        except Exception as e:
            raise DataParseError("Lotte ON Parser Error") from e

    @property
    def discount_params(self):
        return {
            "spdNo": self._basic.get("spdNo"),
            "sitmNo": self._basic.get("sitmNo"),
            "trGrpCd": self._basic.get("trGrpCd"),
            "trNo": self._basic.get("trNo"),
            "lrtrNo": self._data.get("slrInfo").get("trBase").get("lrtrNo")
            if self._data.get("slrInfo") and self._data.get("slrInfo").get("trBase")
            else None,
            "strCd": self._data.get("slrInfo").get("trBase").get("strCd")
            if self._data.get("slrInfo") and self._data.get("slrInfo").get("trBase")
            else None,
            "ctrtTypCd": self._basic.get("ctrtTypCd"),
            "slPrc": self._price.get("slPrc"),
            "slQty": 1,
            "scatNo": self._basic.get("scatNo"),
            "brdNo": self._basic.get("brdNo") if self._basic.get("brdNo") else "",
            "sfcoPdMrgnRt": self._price.get("sfcoPdMrgnRt"),
            "sfcoPdLwstMrgnRt": self._price.get("sfcoPdLwstMrgnRt"),
            "afflPdMrgnRt": Lu.get(self._price, "afflMrgnRt", 0),
            "afflPdLwstMrgnRt": Lu.get(self._price, "afflPdLwstMrgnRt", 0),
            "pcsLwstMrgnRt": Lu.get(self._price, "pcsLwstMrgnRt", 0),
            "infwMdiaCd": "MBL_WEB",
            "chCsfCd": "PA",
            "chTypCd": "PA09",
            "chNo": "0",
            "chDtlNo": "0",
            "aplyStdDttm": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "cartDvsCd": Lu.get(self._data, "dlvInfo.cartDvsCd", "02"),
            "thdyPdYn": "N",
            "dvCst": self._basic.get("dvCst"),
            "fprdDvPdYn": "N",
            "maxPurQty": self._basic.get("maxPurQty"),
            "stkMgtYn": Lu.get(self._stock, "stkMgtYn", "N"),
            "discountApplyProductList": [],
            "screenType": "PRODUCT",
            "dmstOvsDvDvsCd": self._delivery.get("dmstOvsDvDvsCd"),
            "dvPdTypCd": self._delivery.get("dvPdTypCd"),
            "dvCstStdQty": Lu.get(self._delivery, "dvCstStdQty", 0),
            "aplyBestPrcChk": "Y",
            "cpnBoxVersion": "V2",
        }

    @property
    def brand(self):
        return self._basic.get("brdNm")

    @property
    def name(self):
        return self._basic.get("pdNm")

    @property
    def url(self):
        return "https://www.lotteon.com/p/product/{}".format(self._basic.get("pdNo"))

    @property
    def price(self):
        if self._discount is None:
            return ItemPriceData(
                price=self._price.get("slPrc"),
            )
        discount_data = self._discount.get("discountApplyProductList")
        if discount_data is not None and len(discount_data) > 0:
            return ItemPriceData(
                price=self._price.get("slPrc") - discount_data[0].get("dcAmt"),
                original_price=self._price.get("slPrc"),
            )

        return ItemPriceData(
            price=self._price.get("slPrc"),
        )

    @property
    def image(self):
        img = self._images.get("imageList")
        if img and len(img) > 0:
            return img[0].get("origImgFileNm")

    @property
    def category(self):
        return ItemCategoryData(
            [
                self._category.get("dispCatNm0"),
                self._category.get("dispCatNm1"),
                self._category.get("dispCatNm2"),
            ]
        )

    @property
    def description(self):
        return ""

    @property
    def inventory_status(self):
        info = self._data.get("stckInfo")

        if info is None:
            return InventoryStatus.of(is_sold_out=False, stock=999)

        return InventoryStatus.of(is_sold_out=False, stock=info.get("stkQty"))

    @property
    def options(self):
        if self._options:
            return Lu.map(
                self._options,
                lambda x: ItemOptionData(
                    id=x.get("spdNo"),
                    name=x.get("spdNm"),
                    price=x.get("slPrc"),
                    inventory=InventoryStatus.of(
                        is_sold_out=False, stock=Lu.get(x, "stkQty", 9999)
                    ),
                ),
            )
        return []

    @property
    def delivery(self):
        list = self._delivery.get("dvList")

        if list and len(list) > 0:
            for item in list:
                cost = item.get("dvCstInfo")[0] if item.get("dvCstInfo") else None
                if item.get("type") == "TMRW_ON":
                    delivery_type = DeliveryType.EXPRESS_NEXT_DAY
                elif item.get("type") == "SHDST":
                    delivery_type = DeliveryType.EXPRESS_TODAY
                elif item.get("type") == "LNDST":
                    delivery_type = DeliveryType.STANDARD
                else:
                    delivery_type = DeliveryType.STANDARD

                return DeliveryData(
                    delivery_type=delivery_type,
                    price=cost.get("dvCst") if cost else None,
                    threshold_price=cost.get("freeDvStdAmt") if cost else None,
                    pay_type=DeliveryPayType.FREE_OR_PAID
                    if cost
                    else DeliveryPayType.FREE,
                )

        return DeliveryData()

    @property
    def unit(self):
        measure = self._price.get("pdCapa")
        unit = self._price.get("stdUtCd")

        if measure is None or unit is None:
            return ItemUnitData(price=self.price.price)

        return ItemUnitData(
            price=self.price.price / measure, unit_type=ItemUnitType.of(unit), unit=1
        )
