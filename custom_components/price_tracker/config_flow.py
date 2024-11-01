import logging
from copy import deepcopy
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import (
    entity_registry as er
)
from homeassistant.helpers import selector

from .const import CONF_ITEM_REFRESH_INTERVAL, CONF_OPTION_ADD, CONF_OPTION_DELETE, CONF_OPTION_ENTITIES, \
    CONF_OPTION_MODIFY, CONF_OPTION_SELECT, CONF_OPTIONS, CONF_TARGET, DOMAIN, _KIND, CONF_TYPE, CONF_DATA_SCHEMA, \
    CONF_OPTION_DATA_SCHEMA, CONF_ITEM_URL, CONF_ITEM_MANAGEMENT_CATEGORY

_LOGGER = logging.getLogger(__name__)


class PriceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id('price-tracker-{}'.format(user_input[CONF_TYPE]))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title='{}'.format(_KIND[user_input[CONF_TYPE]]),
                                           data={CONF_TARGET: [], CONF_TYPE: user_input[CONF_TYPE]})

        return self.async_show_form(
            step_id="user", data_schema=CONF_DATA_SCHEMA, errors=errors or {}
        )

    async def async_step_import(self, import_info):
        return await self.async_step_user(import_info)

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
                entity = er.async_get(self.hass).async_get(entity_id)
                conf = []
                for k in self.config_entry.options[CONF_TARGET]:
                    if entity.original_name == k.get(CONF_ITEM_URL):
                        conf = k
                        break

                if user_input.get(CONF_OPTION_DELETE):
                    er.async_get(self.hass).async_remove(entity_id=entity_id)
                    try:
                        self.config_entry.options[CONF_TARGET].remove(conf)
                    except:
                        """"""
                    return self.async_create_entry(title=DOMAIN, data=self.config_entry.options)

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
        if user_input is not None:
            data = deepcopy(self.config_entry.options.get(CONF_TARGET, []))
            for item in data[:]:
                if item[CONF_ITEM_URL] == user_input[CONF_ITEM_URL]:
                    data.remove(item)
            data.append({
                CONF_ITEM_URL: user_input[CONF_ITEM_URL],
                CONF_ITEM_MANAGEMENT_CATEGORY: user_input[CONF_ITEM_MANAGEMENT_CATEGORY],
                CONF_ITEM_REFRESH_INTERVAL: user_input[CONF_ITEM_REFRESH_INTERVAL]
            })
            return self.async_create_entry(title=DOMAIN, data={CONF_TARGET: data})

        return self.async_show_form(step_id="entity", data_schema=CONF_OPTION_DATA_SCHEMA, errors={})
