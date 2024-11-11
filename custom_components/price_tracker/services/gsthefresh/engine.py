import json
import logging
import re
from urllib.parse import unquote

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidError, ApiError
from custom_components.price_tracker.services.data import (
    DeliveryData,
    DeliveryPayType,
    ItemData,
    InventoryStatus,
    BooleanType,
)
from custom_components.price_tracker.services.gsthefresh.device import GsTheFreshDevice
from custom_components.price_tracker.utils import find_item, request

_UA = "Dart/3.5 (dart:io)"
_REQUEST_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "appinfo_device_id": "a00000a0fa004cf127333873c60e5b12",
    "device_id": "a00000a0fa004cf127333873c60e5b12",
}
_LOGIN_URL = "https://b2c-bff.woodongs.com/api/bff/v2/auth/accountLogin"
_REAUTH_URL = "https://b2c-apigw.woodongs.com/auth/v1/token/reissue"
_PRODUCT_URL = "https://b2c-apigw.woodongs.com/supermarket/v1/wdelivery/item/{}?pickupItemYn=Y&storeCode={}"
_ITEM_LINK = "https://woodongs.com/link?view=gsTheFreshDeliveryDetail&orderType=pickup&itemCode={}"

_LOGGER = logging.getLogger(__name__)


class GsTheFreshEngine(PriceEngine):
    def __init__(self, item_url: str, device: GsTheFreshDevice):
        self.item_url = item_url
        self.id = GsTheFreshEngine.parse_id(item_url)
        self.device: GsTheFreshDevice = device

    async def load(self) -> ItemData:
        result = await request(
            "get",
            _PRODUCT_URL.format(self.id, self.device.store),
            headers={**_REQUEST_HEADERS, **self.device.headers},
        )
        response = json.loads(result)

        if (
                "data" not in response
                or "weDeliveryItemDetailResultList" not in response["data"]
                or len(response["data"]["weDeliveryItemDetailResultList"]) < 1
        ):
            raise ApiError("GS THE FRESH Response error")

        data = response["data"]["weDeliveryItemDetailResultList"][0]
        _LOGGER.debug(data)
        id = data["itemCode"]
        name = data["indicateItemName"]
        description = data["itemNotification"]
        quantity = data["stockQuantity"] if "stockQuantity" in data else 0
        image = data["weDeliveryItemImageUrl"]
        price = data["normalSalePrice"] - data["totalDiscountRateAmount"]
        sold_out = BooleanType.of(data["soldOutYn"]).value
        url = _ITEM_LINK.format(id)

        delivery_data = response["data"]["processingDeliveryAmountResultList"]
        if delivery_data is not None and len(delivery_data) > 0:
            delivery_price = find_item(delivery_data, "commonCode", 3)
            if delivery_price is not None and delivery_price > 0:
                delivery = DeliveryData(price=delivery_price, type=DeliveryPayType.PAID)
            else:
                delivery = DeliveryData(price=0, type=DeliveryPayType.FREE)
        else:
            delivery = DeliveryData(price=0, type=DeliveryPayType.FREE)

        inventory = (
            InventoryStatus.IN_STOCK
            if quantity > 10
            else InventoryStatus.OUT_OF_STOCK
            if sold_out or quantity <= 0
            else InventoryStatus.ALMOST_SOLD_OUT
        )

        return ItemData(
            id=id,
            name=name,
            original_price=data["normalSalePrice"],
            price=price,
            delivery=delivery,
            image=image,
            url=url,
            description=description,
            inventory=inventory,
        )

    def id(self) -> str:
        return "{}_{}".format(self.device.store, self.id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"itemCode=(?P<product_id>\d+)", unquote(item_url))
        g = u.groupdict()

        if g is None:
            raise InvalidError("GS THE FRESH Item ID Parse(Regex) Error")

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return "gsthefresh"

    @staticmethod
    def engine_name() -> str:
        return "GS THE FRESH"

    def url(self) -> str:
        return self.item_url
