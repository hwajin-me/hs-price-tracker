import hashlib
import json
import logging
from datetime import datetime
from typing import Any

import aiohttp

from custom_components.price_tracker.components.device import PriceTrackerDevice
from custom_components.price_tracker.components.error import ApiError
from custom_components.price_tracker.services.gsthefresh.const import CODE
from custom_components.price_tracker.utilities.request import http_request, default_request_headers

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
CONF_GS_NAVER_LOGIN_FLOW_2_URL = "https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id=VFjv3tsLofatP90P1a5H&client_secret=o2HQ70_GCN&code={}"
CONF_GS_NAVER_LOGIN_FLOW_3_URL = (
    "https://b2c-bff.woodongs.com/api/bff/v2/auth/channelLogin"
)
_LOGGER = logging.getLogger(__name__)


class GsTheFreshLogin:
    """"""

    async def naver_login(self, code: str, device_id: str) -> dict[str, Any]:
        async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            async with session.get(
                    url=CONF_GS_NAVER_LOGIN_FLOW_2_URL.format(code),
                    headers={
                        **default_request_headers(),
                        **_REQUEST_HEADERS
                    },
            ) as response:
                if response.status != 200:
                    raise ApiError("GS THE FRESH - NAVER Response Error")
                naver_response = await response.read()

                if 'access_token' not in json.loads(naver_response):
                    raise ApiError("GS THE FRESH - NAVER Response Error (No access token.)")

                temp_access_token = json.loads(naver_response)["access_token"]

                async with session.post(
                        url=CONF_GS_NAVER_LOGIN_FLOW_3_URL,
                        headers={
                            **default_request_headers(),
                            **_REQUEST_HEADERS,
                            "device_id": device_id,
                            "appinfo_device_id": device_id,
                            "Authorization": "Bearer {}".format(temp_access_token),
                            "content-type": "application/json",
                        },
                        json={"socialType": "naver"},
                ) as login:
                    if login.status != 200:
                        raise ApiError(
                            "GS THE FRESH - Authentication Error {}".format(login)
                        )

                    j = json.loads(await login.read())

                    if "data" not in j \
                            or "accessToken" not in j["data"] \
                            or "refreshToken" not in j["data"] \
                            or "customer" not in j["data"] \
                            or "customerName" not in j["data"]["customer"] \
                            or "customerNumber" not in j["data"]["customer"]:
                        raise ApiError("GS THE FRESH Login API Parse Error - {}".format(j))

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

    async def reauth(self, device_id: str, refresh_token: str) -> dict[str, Any]:
        response = await (await http_request(
            "post",
            _REAUTH_URL,
            headers={
                **REQUEST_DEFAULT_HEADERS,
                **_REQUEST_HEADERS,
                "appinfo_device_id": device_id,
                "device_id": device_id,
                "authorization": "Bearer {}".format(refresh_token),
            },
        )).text()

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


class GsTheFreshDevice(PriceTrackerDevice):

    def __init__(
            self,
            gs_device_id: str,
            access_token: str,
            refresh_token: str,
            name: str,
            number: str,
            store: str,
    ):
        super().__init__(GsTheFreshDevice.device_code(), GsTheFreshDevice.create_device_id(number, store))
        self._gs_device_id = gs_device_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._name = name
        self._number = number
        self._store = store
        self._state = True
        self._updated_at = datetime.now()

    @staticmethod
    def create_device_id(number: str, store: str):
        return "{}-{}".format(number, store)

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

    @staticmethod
    def device_code() -> str:
        return CODE

    @staticmethod
    def device_name() -> str:
        return 'GS THE FRESH'

    async def async_update(self):
        if self._updated_at is None or (datetime.now() - self._updated_at).seconds > (
                60 * 60
        ):
            try:
                self._updated_at = datetime.now()

                data = await GsTheFreshLogin().reauth(
                    self._gs_device_id, self._refresh_token
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
