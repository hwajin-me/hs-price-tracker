import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import unquote

import aiohttp

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidError, ApiError
from custom_components.price_tracker.const import (
    CONF_GS_NAVER_LOGIN_FLOW_2_URL,
    CONF_GS_NAVER_LOGIN_FLOW_3_URL,
    REQUEST_DEFAULT_HEADERS,
)
from custom_components.price_tracker.device import Device
from custom_components.price_tracker.services.data import (
    DeliveryData,
    DeliveryPayType,
    ItemData,
    InventoryStatus,
    BooleanType,
)
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


class GsTheFreshLogin:
    """"""

    async def naver_login(self, code: str, device_id: str) -> dict[str, Any]:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            async with session.get(
                url=CONF_GS_NAVER_LOGIN_FLOW_2_URL.format(code),
                headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS},
            ) as response:
                if response.status != 200:
                    raise Exception("GS THE FRESH - NAVER Response Error")
                naver_response = await response.read()
                temp_access_token = json.loads(naver_response)["access_token"]

                async with session.post(
                    url=CONF_GS_NAVER_LOGIN_FLOW_3_URL,
                    headers={
                        **REQUEST_DEFAULT_HEADERS,
                        **_REQUEST_HEADERS,
                        "device_id": device_id,
                        "appinfo_device_id": device_id,
                        "Authorization": "Bearer {}".format(temp_access_token),
                        "content-type": "application/json",
                    },
                    json={"socialType": "naver"},
                ) as login:
                    if login.status != 200:
                        raise Exception(
                            "GS THE FRESH - Authentication Error {}".format(login)
                        )

                    j = json.loads(await login.read())

                    if "data" not in j:
                        raise Exception("parse error")

                    return {
                        "access_token": j["data"]["accessToken"],
                        "refresh_token": j["data"]["refreshToken"],
                        "name": j["data"]["customer"]["customerName"],
                        "number": j["data"]["customer"]["customerNumber"],
                    }

    async def login(self, device_id: str, username: str, password: str):
        sha256 = hashlib.sha256()
        sha256.update(password.encode())
        hash_password = sha256.hexdigest()
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            async with session.post(
                url=_LOGIN_URL,
                json={"id": username, "password": hash_password},
                headers={
                    **REQUEST_DEFAULT_HEADERS,
                    **_REQUEST_HEADERS,
                    "device_id": device_id,
                    "appinfo_device_id": device_id,
                },
            ) as response:
                if response.status != 200:
                    raise Exception("")

                j = json.loads(await response.read())

                return {
                    "access_token": j["data"]["accessToken"],
                    "refresh_token": j["data"]["refreshToken"],
                    "name": j["data"]["customer"]["customerName"],
                    "number": j["data"]["customer"]["customerNumber"],
                }

    async def reauth(self, device_id: str, access_token: str) -> dict[str, Any]:
        response = await request(
            "post",
            _REAUTH_URL,
            headers={
                **REQUEST_DEFAULT_HEADERS,
                **_REQUEST_HEADERS,
                "appinfo_device_id": device_id,
                "device_id": device_id,
                "authorization": "Bearer {}".format(access_token),
            },
        )

        if "data" in response:
            j = json.loads(response["data"])

            return {
                "access_token": j["data"]["accessToken"],
                "refresh_token": j["data"]["refreshToken"],
                "name": j["data"]["customer"]["customerName"],
                "number": j["data"]["customer"]["customerNumber"],
            }
        else:
            raise ApiError("GS THE FRESH Login(re-authentication) Error")


class GsTheFreshDevice(Device):
    """"""

    def __init__(
        self,
        device_id: str,
        gs_device_id: str,
        access_token: str,
        refresh_token: str,
        name: str,
        number: str,
        store: str,
    ):
        super().__init__("gsthefresh", device_id)
        self._gs_device_id = gs_device_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._name = name
        self._number = number
        self._store = store
        self._state = True
        self._updated_at = datetime.now()

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number

    @property
    def access_token(self):
        return self._access_token

    @property
    def store(self):
        return self._store

    @property
    def icon(self):
        return "mdi:account"

    @property
    def headers(self):
        return {
            "authorization": "Bearer {}".format(self._access_token),
            "device_id": self._gs_device_id,
            "appinfo_device_id": self._gs_device_id,
        }

    async def async_update(self):
        if self._updated_at is None or (datetime.now() - self._updated_at).seconds > (
            60 * 60
        ):
            try:
                self._updated_at = datetime.now()

                data = await GsTheFreshLogin().reauth(
                    self._gs_device_id, self._access_token
                )
                self._access_token = data["access_token"]
                self._refresh_token = data["refresh_token"]
                self._name = data["name"]
                self._number = data["number"]
                self._state = True
                _LOGGER.debug(
                    "GS THE FRESH - Device Update Success {}".format(self._name)
                )
            except Exception as e:
                _LOGGER.error("GS THE FRESH - Device Update Error: {}".format(e))
                self._state = False


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
