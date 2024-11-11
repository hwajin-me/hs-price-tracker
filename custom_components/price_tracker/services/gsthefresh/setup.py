import json
import logging
from datetime import datetime

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.data_entry_flow import AbortFlow

from custom_components.price_tracker.components.error import InvalidError, ApiError
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.gsthefresh.const import CODE
from custom_components.price_tracker.services.gsthefresh.device import GsTheFreshDevice, GsTheFreshLogin
from custom_components.price_tracker.utilities.hash import md5
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.request import http_request_async

_LOGGER = logging.getLogger(__name__)


class GsthefreshSetup(PriceTrackerSetup):
    """"""

    _api_search_mart = 'http://gsthefresh.gsretail.com/thefresh/ko/market-info/find-storelist?searchType=&searchShopName={}&pageNum=1&pageSize=50'

    _conf_gs_naver_login_code = "conf_gs_naver_login_code"
    _conf_gs_store_code_and_name = "conf_gs_store_code_and_name"
    _conf_gs_store_name = "conf_gs_store_name"
    _conf_gs_store_name_like = "conf_gs_store_name_like"

    async def setup(self, user_input: dict = None):
        errors = {}

        # Find mart code by API
        if user_input is None or Lu.get(user_input, self._conf_gs_store_code_and_name) is None:
            return await self.find_mart(user_input=user_input,
                                        search=Lu.get_or_default(user_input, self._conf_gs_store_name_like, ''))

        # Validation
        try:
            if (
                    user_input is not None
                    and self._conf_gs_naver_login_code in user_input
                    and self._conf_gs_store_code_and_name in user_input
                    and user_input[self._conf_gs_naver_login_code] != ""
            ):
                _LOGGER.debug(
                    "GS THE FRESH Setup Validation Passed %s / %s / %s",
                    user_input[self._conf_gs_naver_login_code],
                    user_input[self._conf_gs_store_code_and_name],
                )

                store_code = self._schema_get_gs_mart(user_input)['code']
                device_id = md5('{}-{}'.format(CODE, datetime.now()))
                response = await GsTheFreshLogin().naver_login(code=user_input[self._conf_gs_naver_login_code],
                                                               device_id=device_id)
                unique_id = IdGenerator.generate_device_id(
                    GsTheFreshDevice.create_device_id(number=response['number'], store=store_code)
                )
                devices = {
                    **response,
                    'item_device_id': unique_id,
                    'gs_device_id': device_id,
                    'store': store_code
                }

                await self._config_flow.async_set_unique_id(self._async_set_unique_id(user_input))

                if (
                        entry := self._config_flow.hass.config_entries.async_entry_for_domain_unique_id(
                            self._config_flow.handler, self._config_flow.unique_id
                        )
                ):
                    for already_in_device in entry.data['device']:
                        if already_in_device['item_device_id'] == unique_id:
                            self._config_flow._abort_if_unique_id_configured()
                            return

                    self._config_flow._abort_if_unique_id_configured(
                        updates={**entry.data, 'device': entry.data['device'] + [devices]})

                    return
                else:
                    self._config_flow._abort_if_unique_id_configured()

                return self._config_flow.async_create_entry(title=CODE,
                                                            data={'type': CODE, 'device': [devices]})
        except AbortFlow as e:
            entry = self._config_flow.hass.config_entries.async_entry_for_domain_unique_id(
                self._config_flow.handler, self._config_flow.unique_id
            )
            return self._config_flow.async_create_entry(title=CODE, data=entry.data)
        except ApiError as e:
            _LOGGER.exception('GS THE FRESH Setup Error')
            errors['base'] = 'invalid_code'
        except Exception as e:
            errors['unknown'] = e

        return self._config_flow.async_show_form(
            step_id=self._step_setup,
            description_placeholders={
                **self._form_i18n_title("en", "GS THE FRESH Login Step"),
                **self._form_i18n_title("ja", "GS THE FRESH Login Step"),
                **self._form_i18n_title("ko", "GS THE FRESH 로그인"),
                **self._form_i18n_description(
                    "en",
                    "Open https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id"
                    "=VFjv3tsLofatP90P1a5H&locale=en&oauth_os=ios&redirect_uri=woodongs and copy "
                    'the "Code" query string from the redirected page.',
                ),
                **self._form_i18n_description(
                    "ja",
                    "Open https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id"
                    "=VFjv3tsLofatP90P1a5H&locale=en&oauth_os=ios&redirect_uri=woodongs and copy "
                    'the "Code" query string from the redirected page.',
                ),
                **self._form_i18n_description(
                    "ko",
                    "https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id"
                    '=VFjv3tsLofatP90P1a5H&locale=en&oauth_os=ios&redirect_uri=woodongs 로 이동하신 후 주소창의 "code" 항목을 복사해주십시오.',
                ),
            },
            data_schema=vol.Schema(
                {
                    **self._schema_user_input_service_type(user_input),
                    **self._schema_user_input_gs_mart(user_input),
                    vol.Required(
                        self._conf_gs_naver_login_code, default=None
                    ): cv.string,
                }
            ),
            errors=errors,
        )

    async def find_mart(self, user_input: dict = None, search: str = ''):

        errors = {}

        if search == '' or len(search) < 2:
            if len(search) == 1:
                errors['base'] = 'invalid_search'
        else:
            response = await http_request_async(method='get', url=self._api_search_mart.format(search))
            data = response.text
            if data is None or 'results' not in json.loads(data):
                errors['base'] = 'invalid_search'
            else:
                stores = json.loads(data)['results']
                if len(stores) == 0:
                    errors['base'] = 'no_search_results'
                else:
                    input_result = {}
                    for store in stores:
                        input_result['{}_:_{}'.format(store['shopName'],
                                                      store['shopCode'])] = '{} ({}) - {}'.format(
                            store['shopName'], store['shopCode'], store['address'])

                    return self._config_flow.async_show_form(
                        step_id=self._step_setup,
                        description_placeholders={
                            **self._form_i18n_title("en", "GS THE FRESH Mart Search"),
                            **self._form_i18n_title("ja", "GS THE FRESH Mart Search"),
                            **self._form_i18n_title("ko", "GS THE FRESH 마트 검색"),
                            **self._form_i18n_description(
                                "en",
                                "Please select the mart you want to track.",
                            ),
                            **self._form_i18n_description(
                                "ja",
                                "Please select the mart you want to track.",
                            ),
                            **self._form_i18n_description(
                                "ko",
                                "추적하려는 마트를 선택하십시오.",
                            ),
                        },
                        data_schema=vol.Schema(
                            {
                                **self._schema_user_input_service_type(user_input),
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
                **self._form_i18n_title("en", "GS THE FRESH Mart Search"),
                **self._form_i18n_title("ja", "GS THE FRESH Mart Search"),
                **self._form_i18n_title("ko", "GS THE FRESH 마트 검색"),
                **self._form_i18n_description(
                    "en",
                    "Please enter at least 2 characters to search for the mart.",
                ),
                **self._form_i18n_description(
                    "ja",
                    "Please enter at least 2 characters to search for the mart.",
                ),
                **self._form_i18n_description(
                    "ko",
                    "마트를 검색하려면 최소 2자 이상 입력하십시오.",
                ),
            },
            data_schema=vol.Schema(
                {
                    **self._schema_user_input_service_type(user_input),
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
        return "GS THE FRESH (Korea)"

    def _schema_user_input_gs_mart(self, user_input: dict = None):
        if user_input is None or self._conf_gs_store_code_and_name not in user_input:
            return {}
        return {
            vol.Required(
                self._conf_gs_store_code_and_name,
                description="GS THE FRESH Mart",
                default=user_input[self._conf_gs_store_code_and_name],
            ): vol.In({user_input[self._conf_gs_store_code_and_name]: str(
                user_input[self._conf_gs_store_code_and_name]).replace('_:_', ' ')})
        }

    def _schema_get_gs_mart(self, user_input: dict = None):
        if user_input is None or self._conf_gs_store_code_and_name not in user_input:
            raise InvalidError('GS Mart code not found on {}'.format(user_input))

        data = user_input[self._conf_gs_store_code_and_name].split('_:_')

        return {
            'code': data[1],
            'name': data[0]
        }
