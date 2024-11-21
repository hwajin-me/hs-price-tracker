import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from custom_components.price_tracker.components.device import PriceTrackerDevice
from custom_components.price_tracker.components.error import ApiError, ApiAuthError
from custom_components.price_tracker.services.gsthefresh.const import CODE, NAME
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.request import (
    default_request_headers,
)
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

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
        request = SafeRequest()
        request.headers({**default_request_headers(), **_REQUEST_HEADERS})
        naver_response = await request.request(
            url=CONF_GS_NAVER_LOGIN_FLOW_2_URL.format(code),
        )
        naver_response_json = naver_response.json
        if "access_token" not in naver_response_json:
            raise ApiError("GS THE FRESH - NAVER Response Error (No access token.)")

        request.auth(naver_response_json["access_token"])
        request.headers(
            {
                **default_request_headers(),
                **_REQUEST_HEADERS,
                "device_id": device_id,
                "appinfo_device_id": device_id,
                "content-type": "application/json",
            }
        )
        response = await request.request(
            method=SafeRequestMethod.POST,
            url=CONF_GS_NAVER_LOGIN_FLOW_3_URL,
            data={"socialType": "naver"},
        )

        if response.status_code != 200:
            raise ApiError("GS THE FRESH - Authentication Error {}".format(response))

        j = response.json

        if (
            "data" not in j
            or "accessToken" not in j["data"]
            or "refreshToken" not in j["data"]
            or "customer" not in j["data"]
            or "customerName" not in j["data"]["customer"]
            or "customerNumber" not in j["data"]["customer"]
        ):
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
                    **default_request_headers(),
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
        request = SafeRequest()
        request.headers(
            {
                **default_request_headers(),
                **_REQUEST_HEADERS,
                "appinfo_device_id": device_id,
                "device_id": device_id,
            }
        )
        request.auth(refresh_token)
        http_result = await request.request(
            method=SafeRequestMethod.POST,
            url=_REAUTH_URL,
        )
        response = http_result.json

        if "data" in response:
            j = response["data"]

            return {
                "access_token": j["accessToken"],
                "refresh_token": j["refreshToken"],
            }
        else:
            raise ApiError("GS THE FRESH Login(re-authentication) Error")


class GsTheFreshDevice(PriceTrackerDevice):
    def __init__(
        self,
        entry_id: str,
        gs_device_id: str,
        access_token: str,
        refresh_token: str,
        name: str,
        number: str,
        store: str,
        store_name: str,
    ):
        super().__init__(
            entry_id,
            GsTheFreshDevice.device_code(),
            GsTheFreshDevice.create_device_id(number, store),
        )
        self._gs_device_id = gs_device_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._name = name
        self._number = number
        self._store = store
        self._store_name = store_name
        self._state = True
        self._attr_available = True

    @staticmethod
    def create_device_id(number: str, store: str):
        return "{}-{}".format(number, store)

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return "{}({}) - {}".format(self._store_name, self._store, self._name)

    @property
    def number(self):
        return self._number

    @property
    def store(self):
        return self._store

    @property
    def icon(self):
        return "mdi:account"

    @property
    def headers(self):
        return {
            "device_id": self._gs_device_id,
            "appinfo_device_id": self._gs_device_id,
        }

    @property
    def access_token(self):
        return self._access_token

    @property
    def refresh_token(self):
        return self._refresh_token

    @staticmethod
    def device_code() -> str:
        return CODE

    @staticmethod
    def device_name() -> str:
        return NAME

    async def reauth(self):
        try:
            data = await GsTheFreshLogin().reauth(
                self._gs_device_id, self._refresh_token
            )

            entry = self.hass.config_entries.async_get_entry(self._entry_id)
            entry_data = entry.data
            new_entry_data = (
                {"device": []} if entry_data is None else {"device": [], **entry_data}
            )
            if entry_data is not None and "device" in new_entry_data:
                actual = {
                    **Lu.get_item_or_default(
                        new_entry_data["device"],
                        "item_device_id",
                        self._generate_device_id,
                        {},
                    )
                }
                new_entry_data["device"] = Lu.remove_item(
                    new_entry_data["device"], "item_device_id", self._generate_device_id
                )
                new_entry_data["device"].append(
                    {
                        **actual,
                        **{
                            "access_token": data["access_token"],
                            "refresh_token": data["refresh_token"],
                        },
                    }
                )

            if new_entry_data != {}:
                self.hass.config_entries.async_update_entry(
                    self.hass.config_entries.async_get_entry(self._entry_id),
                    data={**new_entry_data},
                )

            self._access_token = data["access_token"]
            self._refresh_token = data["refresh_token"]
            self._state = True
            self._attr_available = True
            self._updated_at = datetime.now()
            _LOGGER.debug(
                "GS THE FRESH - Device Update Success {}, {} / {}".format(
                    self._generate_device_id, self._access_token, self._refresh_token
                )
            )
        except ApiAuthError as e:
            _LOGGER.error(
                "GS THE FRESH - Device Update Error Auth: {} / {}".format(
                    self._generate_device_id, e
                )
            )
            self._state = False
            self._attr_available = False
            self._updated_at = datetime.now() - timedelta(minutes=1)
        except Exception as e:
            _LOGGER.exception(
                "GS THE FRESH - Device Update Error: {}, {}".format(
                    self._generate_device_id, e
                )
            )
            self._state = False
            self._attr_available = False
            self._updated_at = datetime.now() - timedelta(minutes=1)

        self._attr_extra_state_attributes = {
            "store_name": self._store_name,
            "store": self._store,
            "name": self._name,
            "number": self._number,
            "updated_at": self._updated_at,
        }

    def invalid(self):
        self._state = False
        self._attr_available = False
        self._updated_at = datetime.now()

    async def async_update(self):
        if (
            self._updated_at is None
            or (datetime.now() - self._updated_at).seconds > (60 * 60 * 3)
            or self._attr_available is False
        ):
            await self.reauth()
        else:
            _LOGGER.debug("GS THE FRESH - Device Update Skipped")
