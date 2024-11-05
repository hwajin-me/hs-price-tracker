import logging
from copy import deepcopy
from typing import Any, Dict, Optional

from custom_components.price_tracker.utils import findItem, findValueOrDefault
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import (
    entity_registry as er
)
from homeassistant.helpers import selector

from .const import CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR, CONF_ITEM_REFRESH_INTERVAL, CONF_ITEM_UNIT, CONF_ITEM_UNIT_PRICE, CONF_ITEM_UNIT_TYPE, CONF_ITEM_UNIT_TYPE_KIND, CONF_OPTION_ADD, CONF_OPTION_DELETE, CONF_OPTION_ENTITIES, \
    CONF_OPTION_MODIFY, CONF_OPTION_SELECT, CONF_OPTIONS, CONF_TARGET, DOMAIN, _KIND, CONF_TYPE, CONF_DATA_SCHEMA, \
    CONF_OPTION_DATA_SCHEMA, CONF_ITEM_URL, CONF_ITEM_MANAGEMENT_CATEGORY, CONF_GS_NAVER_LOGIN_FLOW_1_URL

_LOGGER = logging.getLogger(__name__)


class PriceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            if user_input[CONF_TYPE] == 'gsthefresh':
                return await self.async_step_gs_login()

            await self.async_set_unique_id('price-tracker-{}'.format(user_input[CONF_TYPE]))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title='{}'.format(_KIND[user_input[CONF_TYPE]]),
                                           options={CONF_TARGET: [], CONF_TYPE: user_input[CONF_TYPE]})

        return self.async_show_form(
            step_id="user", data_schema=CONF_DATA_SCHEMA, errors=errors or {}
        )

    async def async_step_import(self, import_info):
        return await self.async_step_user(import_info)

    async def async_step_gs_login(self, user_input=None):
        _LOGGER.debug("async_step_gs_login")
        if not user_input:
            return self.async_external_step(
                step_id="gs_login",
                url=CONF_GS_NAVER_LOGIN_FLOW_1_URL
            )
        if user_input is not None:
            """Check if the provided credentials are valid."""

        return self.async_show_form(
            step_id="gs_login", data_schema=vol.Schema({
                vol.Required(CONF_ITEM_URL, default=None): cv.string,
                vol.Optional(CONF_ITEM_MANAGEMENT_CATEGORY, default=None): cv.string,
                vol.Required(CONF_ITEM_REFRESH_INTERVAL, default=10): cv.positive_int
            }), errors={}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PriceTrackerOptionsFlowHandler(config_entry)


class PriceTrackerOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict = None) -> dict:
        errors = {}

        if user_input is not None:
            if not errors:
                if user_input.get(CONF_OPTION_SELECT) == CONF_OPTION_MODIFY:
                    return await self.async_step_select()
                elif user_input.get(CONF_OPTION_SELECT) == CONF_OPTION_ADD:
                    return await self.async_step_entity()

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_OPTION_SELECT): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=CONF_OPTIONS, mode=selector.SelectSelectorMode.LIST,
                                                  translation_key=CONF_OPTION_SELECT)),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )

    async def async_step_select(self, user_input: dict = None):
        errors = {}

        if user_input is not None and user_input.get(CONF_OPTION_ENTITIES) is not None:
            if not errors:
                entity_id = user_input.get(CONF_OPTION_ENTITIES)
                hass = er.async_get(self.hass)
                entity = hass.async_get(entity_id)

                if user_input.get(CONF_OPTION_DELETE):
                    hass.async_remove(entity_id=entity_id)
                    return self.async_create_entry(title=DOMAIN, data={CONF_TARGET: list(filter(lambda x : entity.original_name != x[CONF_ITEM_URL], self.config_entry.options[CONF_TARGET]))})
                else:

                    return await self.async_step_entity(user_input={
                        CONF_OPTION_MODIFY: entity,
                    })

        option_entities = []
        entities = er.async_entries_for_config_entry(
            er.async_get(self.hass), self.config_entry.entry_id)
        for e in entities:
            option_entities.append(e.entity_id)

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_OPTION_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(include_entities=option_entities)),
                vol.Optional(CONF_OPTION_DELETE): selector.BooleanSelector(selector.BooleanSelectorConfig())
            }
        )

        return self.async_show_form(
            step_id="select", data_schema=options_schema, errors=errors
        )

    async def async_step_entity(self, user_input: dict = None):

        if user_input is not None and CONF_OPTION_MODIFY in user_input:
            item = findItem(self.config_entry.options[CONF_TARGET], CONF_ITEM_URL, user_input[CONF_OPTION_MODIFY].original_name)

            if item is None:
                raise ("Not found")

            return self.async_show_form(step_id="entity", data_schema=vol.Schema({
                vol.Required(CONF_ITEM_URL, default=item[CONF_ITEM_URL]): cv.string,
                vol.Optional(CONF_ITEM_MANAGEMENT_CATEGORY, default=findValueOrDefault(item, CONF_ITEM_MANAGEMENT_CATEGORY, '')): cv.string,
                vol.Optional(CONF_ITEM_UNIT_TYPE, default=findValueOrDefault(item, CONF_ITEM_UNIT_TYPE, 'piece')): vol.In(CONF_ITEM_UNIT_TYPE_KIND),
                vol.Optional(CONF_ITEM_UNIT_PRICE, default=findValueOrDefault(item, CONF_ITEM_UNIT_PRICE, 0)): cv.positive_int,
                vol.Optional(CONF_ITEM_UNIT, default=findValueOrDefault(item, CONF_ITEM_UNIT, 1)): cv.positive_int,
                vol.Required(CONF_ITEM_REFRESH_INTERVAL, default=findValueOrDefault(item    , CONF_ITEM_REFRESH_INTERVAL, 10)): cv.positive_int,
                vol.Required(CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR, default=24): cv.positive_int,
            }), errors={})

        if user_input is not None:
            data = deepcopy(self.config_entry.options.get(CONF_TARGET, []))
            for item in data[:]:
                if item[CONF_ITEM_URL] == user_input[CONF_ITEM_URL]:
                    data.remove(item)
            data.append({
                CONF_ITEM_URL: user_input[CONF_ITEM_URL],
                CONF_ITEM_MANAGEMENT_CATEGORY: user_input[CONF_ITEM_MANAGEMENT_CATEGORY] if CONF_ITEM_MANAGEMENT_CATEGORY in user_input else None,
                CONF_ITEM_UNIT_TYPE: user_input[CONF_ITEM_UNIT_TYPE] if CONF_ITEM_UNIT_TYPE in user_input else 'piece',
                CONF_ITEM_UNIT_PRICE: user_input[CONF_ITEM_UNIT_PRICE] if CONF_ITEM_UNIT_PRICE in user_input and user_input[CONF_ITEM_UNIT_PRICE] != 0 else 0,
                CONF_ITEM_UNIT: user_input[CONF_ITEM_UNIT] if CONF_ITEM_UNIT in user_input and user_input[CONF_ITEM_UNIT] != 0 else 0,
                CONF_ITEM_REFRESH_INTERVAL: user_input[CONF_ITEM_REFRESH_INTERVAL],
                CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR: user_input[CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR] if CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR in user_input and user_input[CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR] >= 1 else 24,
            })
            return self.async_create_entry(title=DOMAIN, data={CONF_TARGET: data})

        return self.async_show_form(step_id="entity", data_schema=CONF_OPTION_DATA_SCHEMA, errors={})
