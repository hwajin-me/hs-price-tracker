import json
import logging
from datetime import datetime

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.data_entry_flow import AbortFlow

from custom_components.price_tracker.components.error import InvalidError, ApiError
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.components.lang import Lang
from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.gsthefresh.const import CODE, NAME
from custom_components.price_tracker.services.gsthefresh.device import (
    GsTheFreshDevice,
    GsTheFreshLogin,
)
from custom_components.price_tracker.utilities.hash import md5
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_LOGGER = logging.getLogger(__name__)


class GsthefreshSetup(PriceTrackerSetup):
    """"""

    _api_search_mart = "http://gsthefresh.gsretail.com/thefresh/ko/market-info/find-storelist?searchType=&searchShopName={}&pageNum=1&pageSize=100"
    _login_url = "https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id=VFjv3tsLofatP90P1a5H&locale=en&oauth_os=ios&redirect_uri=woodongs"
    _conf_gs_naver_login_code = "conf_gs_naver_login_code"
    _conf_gs_store_code_and_name = "conf_gs_store_code_and_name"
    _conf_gs_store_name = "conf_gs_store_name"
    _conf_gs_store_name_like = "conf_gs_store_name_like"

    async def setup(self, user_input: dict = None):
        errors = {}

        # Find mart code by API
        if (
            user_input is None
            or Lu.get(user_input, self._conf_gs_store_code_and_name) is None
        ):
            return await self.find_mart(
                user_input=user_input,
                search=Lu.get_or_default(user_input, self._conf_gs_store_name_like, ""),
            )

        # Validation
        try:
            if (
                user_input is not None
                and self._conf_gs_naver_login_code in user_input
                and self._conf_gs_store_code_and_name in user_input
                and user_input[self._conf_gs_naver_login_code] != ""
            ):
                _LOGGER.debug(
                    "GS THE FRESH Setup Validation Passed %s / %s",
                    user_input[self._conf_gs_naver_login_code],
                    user_input[self._conf_gs_store_code_and_name],
                )

                store_code = self._schema_get_gs_mart(user_input)["code"]
                device_id = md5("{}-{}".format(CODE, datetime.now()))
                response = await GsTheFreshLogin().naver_login(
                    code=user_input[self._conf_gs_naver_login_code], device_id=device_id
                )
                unique_id = IdGenerator.generate_device_id(
                    GsTheFreshDevice.create_device_id(
                        number=response["number"], store=store_code
                    )
                )
                devices = {
                    **response,
                    "item_device_id": unique_id,
                    "gs_device_id": device_id,
                    "store": store_code,
                    "store_name": self._schema_get_gs_mart(user_input)["name"],
                }

                await self._config_flow.async_set_unique_id(
                    self._async_set_unique_id(user_input)
                )

                if (
                    entry
                    := self._config_flow.hass.config_entries.async_entry_for_domain_unique_id(
                        self._config_flow.handler, self._config_flow.unique_id
                    )
                ):
                    self._config_flow._abort_if_unique_id_configured(
                        updates={
                            **entry.data,
                            self.conf_proxy: Lu.get(entry.data, self.conf_proxy, []),
                            self.conf_proxy_list: Lu.get(
                                entry.data, self.conf_proxy_list, []
                            ),
                            self.conf_proxy_opensource_use: Lu.get(
                                entry.data, self.conf_proxy_opensource_use, False
                            ),
                            "device": Lu.remove_item(
                                entry.data["device"], "item_device_id", unique_id
                            )
                            + [devices],
                        }
                    )
                else:
                    self._config_flow._abort_if_unique_id_configured()

                return self._config_flow.async_create_entry(
                    title=self.setup_name(),
                    data={
                        "type": CODE,
                        "device": [devices],
                        self.conf_proxy: Lu.get(user_input, self.conf_proxy, []),
                        self.conf_proxy_list: Lu.get(
                            user_input, self.conf_proxy_list, []
                        ),
                        self.conf_proxy_opensource_use: Lu.get(
                            entry.data, self.conf_proxy_opensource_use, False
                        ),
                    },
                    options=dict(entry.options if entry is not None else {}),
                )
        except AbortFlow as e:
            _LOGGER.warning("GS THE FRESH Setup AbortFlow (might be duplicate) %s", e)
            entry = (
                self._config_flow.hass.config_entries.async_entry_for_domain_unique_id(
                    self._config_flow.handler, self._config_flow.unique_id
                )
            )
            return self._config_flow.async_create_entry(
                title=self.setup_name(),
                data=dict(entry.data),
                options=dict(entry.options if entry is not None else {}),
            )
        except ApiError as e:
            _LOGGER.exception("GS THE FRESH Setup Error %s", e)
            errors["base"] = "invalid_code"
        except Exception as e:
            _LOGGER.exception("GS THE FRESH Setup Error")
            errors["unknown"] = e

        return self._config_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **Lang(self._config_flow.hass)
                .select(user_input)
                .f(
                    key="title",
                    items={
                        "en": "GS THE FRESH Login",
                        "ja": "GS THE FRESH ログイン",
                        "ko": "GS THE FRESH 로그인",
                    },
                ),
                **Lang(self._config_flow.hass)
                .select(user_input)
                .f(
                    key="description",
                    items={
                        "en": "Please enter the code you copied from the "
                        + self._login_url
                        + "page. The code is in the query string which is the part after the 'code='.",
                        "ja": self._login_url
                        + " からコピーしたコードを入力してください。コードは「code=」の後にあるクエリ文字列の一部です。",
                        "ko": self._login_url
                        + " 페이지에서 복사한 코드를 입력하십시오. 코드는 'code=' 이후의 쿼리 문자열입니다.",
                    },
                ),
            },
            data_schema=vol.Schema(
                {
                    **self._schema_user_input_service_type(user_input),
                    **self._schema_user_input_gs_mart(user_input),
                    **Lang(self._config_flow.hass).selector(user_input),
                    vol.Required(
                        self._conf_gs_naver_login_code, default=None
                    ): cv.string,
                }
            ),
            errors=errors,
        )

    async def find_mart(self, user_input: dict = None, search: str = ""):
        errors = {}

        if search == "" or len(search) < 2:
            if len(search) == 1:
                errors["base"] = "invalid_search"
        else:
            request = SafeRequest()
            response = await request.request(
                method=SafeRequestMethod.GET, url=self._api_search_mart.format(search)
            )
            data = response.data
            if data is None or "results" not in json.loads(data):
                errors["base"] = "invalid_search"
            else:
                stores = json.loads(data)["results"]
                if len(stores) == 0:
                    errors["base"] = "no_search_results"
                else:
                    input_result = {}
                    for store in stores:
                        input_result[
                            "{}_:_{}".format(store["shopName"], store["shopCode"])
                        ] = "{} ({}) - {}".format(
                            store["shopName"], store["shopCode"], store["address"]
                        )

                    return self._config_flow.async_show_form(
                        step_id=self._step_setup,
                        description_placeholders={
                            **Lang(self._config_flow.hass)
                            .select(user_input)
                            .f(
                                key="title",
                                items={
                                    "en": "GS THE FRESH Mart Search",
                                    "ja": "GS THE FRESHのマートを検索",
                                    "ko": "GS THE FRESH 마트 검색",
                                },
                            ),
                            **Lang(self._config_flow.hass)
                            .select(user_input)
                            .f(
                                key="description",
                                items={
                                    "en": "Please select the mart you want to track.",
                                    "ja": "検索したいマートを選択してください。",
                                    "ko": "추적하려는 마트를 선택하십시오.",
                                },
                            ),
                        },
                        data_schema=vol.Schema(
                            {
                                **self._schema_user_input_service_type(user_input),
                                **Lang(self._config_flow.hass).selector(user_input),
                                vol.Required(
                                    self._conf_gs_store_code_and_name, default=None
                                ): vol.In(input_result),
                            }
                        ),
                        errors=errors,
                    )

        return self._config_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **Lang(self._config_flow.hass)
                .select(user_input)
                .f(
                    key="title",
                    items={
                        "en": "GS THE FRESH Mart Search",
                        "ja": "GS THE FRESHのマートを検索",
                        "ko": "GS THE FRESH 마트 검색",
                    },
                ),
                **Lang(self._config_flow.hass)
                .select(user_input)
                .f(
                    key="description",
                    items={
                        "en": "Please enter at least 2 characters to search for the mart.",
                        "ja": "マートを検索するには、少なくとも2文字を入力してください。",
                        "ko": "마트를 검색하려면 최소 2자 이상 입력하십시오.",
                    },
                ),
            },
            data_schema=vol.Schema(
                {
                    **self._schema_user_input_service_type(user_input),
                    **Lang(self._config_flow.hass).selector(user_input),
                    vol.Required(
                        self._conf_gs_store_name_like, default=None
                    ): cv.string,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME

    def _schema_user_input_gs_mart(self, user_input: dict = None):
        if user_input is None or self._conf_gs_store_code_and_name not in user_input:
            return {}
        return {
            vol.Required(
                self._conf_gs_store_code_and_name,
                description="GS THE FRESH Mart",
                default=user_input[self._conf_gs_store_code_and_name],
            ): vol.In(
                {
                    user_input[self._conf_gs_store_code_and_name]: str(
                        user_input[self._conf_gs_store_code_and_name]
                    ).replace("_:_", " ")
                }
            )
        }

    def _schema_get_gs_mart(self, user_input: dict = None):
        if user_input is None or self._conf_gs_store_code_and_name not in user_input:
            raise InvalidError("GS Mart code not found on {}".format(user_input))

        data = user_input[self._conf_gs_store_code_and_name].split("_:_")

        return {"code": data[1], "name": data[0]}
