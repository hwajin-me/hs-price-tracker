import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.gsthefresh.const import CODE

_LOGGER = logging.getLogger(__name__)


class GsthefreshSetup(PriceTrackerSetup):
    """"""

    _conf_gs_naver_login_code = "conf_gs_naver_login_code"
    _conf_gs_store_code = "conf_gs_store_code"
    _conf_item_device_code = "conf_item_device_code"

    async def setup(self, user_input: dict = None):
        # Validation
        if (
            user_input is not None
            and self._conf_gs_naver_login_code in user_input
            and self._conf_gs_store_code in user_input
            and self._conf_item_device_code in user_input
            and user_input[self._conf_gs_naver_login_code] != ""
        ):
            _LOGGER.debug(
                "GS THE FRESH Setup Validation Passed %s / %s / %s",
                user_input[self._conf_gs_naver_login_code],
                user_input[self._conf_gs_store_code],
                user_input[self._conf_item_device_code],
            )

            await self._config_flow.async_set_unique_id(
                self._async_set_unique_id(user_input)
            )

        return self._config_flow.async_show_form(
            step_id="setup",
            description_placeholders={
                **self._form_i18n_title("en", "GS THE FRESH Login Step"),
                **self._form_i18n_title("ko", "GS THE FRESH 로그인"),
                **self._form_i18n_description(
                    "en",
                    "Open https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id"
                    "=VFjv3tsLofatP90P1a5H&locale=en&oauth_os=ios&redirect_uri=woodongs and copy "
                    'the "Code" query string from the redirected page. Store code can be found in the URL of https://github.com/miumida/mart_holiday',
                ),
                **self._form_i18n_description(
                    "ko",
                    "https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id"
                    '=VFjv3tsLofatP90P1a5H&locale=en&oauth_os=ios&redirect_uri=woodongs 로 이동하신 후 주소창의 "code" 항목을 복사해주십시오. 마트코드(store code)는 https://github.com/miumida/mart_holiday 를 참고해주십시오.',
                ),
            },
            data_schema=vol.Schema(
                {
                    **self._schema_user_input_service_type(user_input),
                    vol.Required(
                        self._conf_gs_naver_login_code, default=None
                    ): cv.string,
                    vol.Required(self._conf_gs_store_code, default=None): cv.string,
                    vol.Required(self._conf_item_device_code, default=None): cv.string,
                }
            ),
            errors={},
        )

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return "GS THE FRESH (Korea)"
