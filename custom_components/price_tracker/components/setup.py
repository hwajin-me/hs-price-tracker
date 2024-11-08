import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from custom_components.price_tracker.const import CONF_TYPE

import logging


_LOGGER = logging.getLogger(__name__)


class PriceTrackerSetup:
    _step_setup: str = 'setup'  # static variable
    _config_flow: config_entries.ConfigFlow
    _option_flow: config_entries.OptionsFlow
    _option_setup_select: str = 'option_setup_select'
    _option_modify_select: str = 'option_modify_select'
    _option_add_select: str = 'option_add_select'

    def __init__(self, config_flow: config_entries.ConfigFlow = None, option_flow: config_entries.OptionsFlow = None):
        self._config_flow = config_flow
        self._option_flow = option_flow

    async def setup(self, user_input: dict = None):
        _LOGGER.debug("Setup(configuration): %s", user_input)

        if user_input is None:
            return None

        await self._config_flow.async_set_unique_id(self._async_set_unique_id(user_input))
        self._config_flow._abort_if_unique_id_configured()

        return self._config_flow.async_create_entry(title=self.setup_name(), data={**self.setup_config_data(user_input)})

    async def option_setup(self, user_input: dict = None):
        _LOGGER.debug("Setup(option): %s", user_input)

        return self._option_flow.async_show_form(
            step_id=self._step_setup, data_schema=vol.Schema(
                {
                    vol.Optional(self._option_setup_select): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=[
                            self._option_modify_select,
                            self._option_add_select
                        ], mode=selector.SelectSelectorMode.LIST,
                            translation_key=self._option_setup_select)),
                },
                **self._schema_user_input_option_service_device(user_input)
            ), errors={}
        )

    async def option_modify(self, user_input: dict = None):
        """Modify an existing entry."""

        if user_input is None:
            """Select an entity(device)"""
            return None

    async def option_add(self, user_input: dict = None):
        pass

    async def option_select_device(self):
        pass

    async def option_select_entity(self):
        pass

    def setup_config_data(self, user_input: dict = None) -> dict:
        return {
            CONF_TYPE: user_input['service_type']
        }

    @staticmethod
    def setup_code() -> str:
        pass

    @staticmethod
    def setup_name() -> str:
        pass

    def _get_data(self):
        return self._config_flow.hass.config_entries.async_entry_for_domain_unique_id(
            self._config_flow.handler, self._config_flow.unique_id
        )

    def _async_set_unique_id(self, user_input: dict) -> str:
        return "price-tracker-{}".format(user_input['service_type'])

    def _schema_user_input_service_type(self, user_input: dict = None):
        if user_input is None or 'service_type' not in user_input:
            return {}

        return {vol.Required('service_type', description='Service Type', default=user_input['service_type']): vol.In(
            {user_input['service_type']: user_input['service_type']})}

    def _schema_user_input_option_service_device(self, user_input: dict = None):
        if user_input is None or 'service_device' not in user_input:
            return {}

        return {vol.Required('service_device', description='Target Device', default=user_input['service_device']): vol.In(
            {user_input['service_device']: user_input['service_device']})}

    def _option_device(self, user_input: dict = None):
        if user_input is None:
            return None

        if 'service_device' not in user_input:
            return None

        return user_input['service_device']

    def _form_i18n_description(self, lang: str, description: str) -> dict:
        return {
            'description_{}'.format(lang): description
        }

    def _form_i18n_title(self, lang: str, item: str) -> dict:
        return {
            'title_{}'.format(lang): item
        }
