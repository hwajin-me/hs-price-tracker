import logging
from datetime import datetime
from typing import Any, Dict, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from custom_components.price_tracker.services.gsthefresh.engine import GsTheFreshLogin
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utils import md5
from .components.error import UnsupportedError
from .components.setup import PriceTrackerSetup
from .const import (
    CONF_DEVICE,
    CONF_GS_NAVER_LOGIN_CODE,
    CONF_GS_STORE_CODE,
    CONF_ITEM_DEVICE_CODE,
    CONF_TARGET,
    DOMAIN,
    _KIND,
    CONF_TYPE,
)
from .services.setup import (
    price_tracker_setup_service,
    price_tracker_setup_service_user_input,
    price_tracker_setup_init,
    price_tracker_setup_option_service,
)

_LOGGER = logging.getLogger(__name__)


class PriceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    data: Optional[Dict[str, Any]]

    async def async_step_reconfigure(self, user_input: dict = None):
        pass

    async def async_migrate_entry(
        self, hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Migrate old entry."""
        _LOGGER.debug("Migrate entry (config-flow)")

        return False

    async def async_step_import(self, import_info):
        return await self.async_step_user(import_info)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PriceTrackerOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors: dict = {}

        try:
            if step := price_tracker_setup_service(
                service_type=price_tracker_setup_service_user_input(user_input),
                config_flow=self,
            ):
                return await step.setup(user_input)
        except UnsupportedError:
            errors["base"] = "unsupported"

        return self.async_show_form(
            step_id="user", data_schema=price_tracker_setup_init(), errors=errors
        )

    async def async_step_setup(self, user_input=None):
        """Set-up flows."""
        raise NotImplementedError("Not implemented (Set up). {}".format(user_input))

    async def async_step_gs_login(self, user_input=None):
        type = "gsthefresh"
        if user_input is not None:
            await self.async_set_unique_id("price-tracker-{}".format(type))
            device_id = md5("gsthefresh-{}".format(datetime.now()))
            response = await GsTheFreshLogin().naver_login(
                code=user_input[CONF_GS_NAVER_LOGIN_CODE], device_id=device_id
            )
            devices = {
                **response,
                "device_id": user_input[CONF_ITEM_DEVICE_CODE],
                "gs_device_id": device_id,
                "store": user_input[CONF_GS_STORE_CODE],
            }

            if entry := self.hass.config_entries.async_entry_for_domain_unique_id(
                self.handler, self.unique_id
            ):
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_TYPE: type,
                        CONF_DEVICE: entry.data[CONF_DEVICE] + [devices],
                    }
                )
            else:
                self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="{}".format(_KIND[type]),
                data={CONF_TARGET: [], CONF_TYPE: type, CONF_DEVICE: [devices]},
            )

        return self.async_show_form(
            step_id="gs_login",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GS_NAVER_LOGIN_CODE, default=None): cv.string,
                    vol.Required(CONF_GS_STORE_CODE, default=None): cv.string,
                    vol.Required(CONF_ITEM_DEVICE_CODE, default=None): cv.string,
                }
            ),
            errors={},
        )


class PriceTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self.setup: PriceTrackerSetup = price_tracker_setup_option_service(
            service_type=self.config_entry.data[CONF_TYPE],
            option_flow=self,
            config_entry=config_entry,
        )

    async def async_step_init(self, user_input: dict = None) -> dict:
        """Delegate step"""
        return await self.setup.option_setup(user_input)

    async def async_step_setup(self, user_input: dict = None):
        """Set-up flows."""

        # Select option (1)
        if user_input is None:
            return await self.setup.option_setup(user_input)

        # 1
        if self.setup.const_option_setup_select in user_input:
            if self.setup.const_option_select_device not in user_input:
                device = await self.setup.option_select_device(user_input)
                if device is not None:
                    return device

        if (
            Lu.get(user_input, self.setup.const_option_setup_select)
            == self.setup.const_option_modify_select
            and Lu.get(user_input, self.setup.const_option_select_entity) is None
        ):
            return await self.setup.option_select_entity(
                device=Lu.get(user_input, self.setup.const_option_select_device),
                user_input=user_input,
            )

        # 2
        if self.setup.const_option_setup_select in user_input:
            if (
                user_input[self.setup.const_option_setup_select]
                == self.setup.const_option_modify_select
            ):
                return await self.setup.option_modify(
                    device=Lu.get(user_input, self.setup.const_option_select_device),
                    entity=Lu.get(user_input, self.setup.const_option_select_entity),
                    user_input=user_input,
                )
            elif (
                user_input[self.setup.const_option_setup_select]
                == self.setup.const_option_add_select
            ):
                return await self.setup.option_upsert(
                    device=Lu.get(user_input, self.setup.const_option_select_device),
                    user_input=user_input,
                )

        raise NotImplementedError("Not implemented (Set up). {}".format(user_input))
