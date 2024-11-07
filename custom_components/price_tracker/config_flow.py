import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers import selector

from custom_components.price_tracker.engine.gsthefresh.gsthefresh import GsTheFreshLogin
from custom_components.price_tracker.utils import findItem, findValueOrDefault, md5
from .const import CONF_DEVICE, CONF_GS_NAVER_LOGIN_CODE, CONF_GS_STORE_CODE, \
    CONF_ITEM_DEVICE_CODE, \
    CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR, \
    CONF_ITEM_REFRESH_INTERVAL, CONF_ITEM_UNIT, CONF_ITEM_UNIT_PRICE, CONF_ITEM_UNIT_TYPE, CONF_ITEM_UNIT_TYPE_KIND, \
    CONF_OPTION_ADD, CONF_OPTION_DELETE, CONF_OPTION_ENTITIES, \
    CONF_OPTION_MODIFY, CONF_OPTION_SELECT, CONF_OPTIONS, CONF_TARGET, DOMAIN, _KIND, CONF_TYPE, CONF_DATA_SCHEMA, \
    CONF_ITEM_URL, CONF_ITEM_MANAGEMENT_CATEGORY, CONF_OPTION_DEVICES

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
                                           data={CONF_TARGET: [],
                                                 CONF_TYPE: user_input[CONF_TYPE],
                                                 CONF_DEVICE: []})

        return self.async_show_form(
            step_id="user", data_schema=CONF_DATA_SCHEMA, errors=errors or {}
        )

    async def async_step_import(self, import_info):
        return await self.async_step_user(import_info)

    async def async_step_gs_login(self, user_input=None):

        type = 'gsthefresh'
        if user_input is not None:
            await self.async_set_unique_id('price-tracker-{}'.format(type))
            device_id = md5("gsthefresh-{}".format(datetime.now()))
            response = await GsTheFreshLogin().naver_login(code=user_input[CONF_GS_NAVER_LOGIN_CODE],
                                                           device_id=device_id)
            devices = {**response, 'device_id': user_input[CONF_ITEM_DEVICE_CODE], 'gs_device_id': device_id,
                       'store': user_input[CONF_GS_STORE_CODE]}

            if (
                    entry := self.hass.config_entries.async_entry_for_domain_unique_id(
                        self.handler, self.unique_id
                    )
            ):
                self._abort_if_unique_id_configured(
                    updates={CONF_TYPE: type, CONF_DEVICE: entry.data[CONF_DEVICE] + [devices]})
            else:
                self._abort_if_unique_id_configured()

            return self.async_create_entry(title='{}'.format(_KIND[type]),
                                           data={CONF_TARGET: [], CONF_TYPE: type, CONF_DEVICE: [devices]})

        return self.async_show_form(
            step_id="gs_login", data_schema=vol.Schema({
                vol.Required(CONF_GS_NAVER_LOGIN_CODE, default=None): cv.string,
                vol.Required(CONF_GS_STORE_CODE, default=None): cv.string,
                vol.Required(CONF_ITEM_DEVICE_CODE, default=None): cv.string,
            }), errors={}
        )

    async def async_step_reconfigure(self, user_input: dict = None):
        """"""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PriceTrackerOptionsFlowHandler(config_entry)


class PriceTrackerOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict = None) -> dict:
        errors = {}

        if CONF_DEVICE in self.config_entry.data and len(self.config_entry.data[CONF_DEVICE]) > 0:
            if user_input is None:
                device_entitites = []

                for d in dr.async_entries_for_config_entry(dr.async_get(self.hass), self.config_entry.entry_id):
                    device_entitites.append(d.serial_number)

                return self.async_show_form(
                    step_id="init", data_schema=vol.Schema({
                        vol.Optional(CONF_OPTION_DEVICES): vol.In(device_entitites),
                    }), errors=errors)

        if user_input is not None:
            if not errors:
                if user_input.get(CONF_OPTION_SELECT) == CONF_OPTION_MODIFY:
                    return await self.async_step_select(
                        user_input={CONF_OPTION_DEVICES: user_input.get(CONF_OPTION_DEVICES)})
                elif user_input.get(CONF_OPTION_SELECT) == CONF_OPTION_ADD:
                    return await self.async_step_entity(
                        user_input={CONF_OPTION_DEVICES: user_input.get(CONF_OPTION_DEVICES)})

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_OPTION_SELECT): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=CONF_OPTIONS, mode=selector.SelectSelectorMode.LIST,
                                                  translation_key=CONF_OPTION_SELECT)),
            }
        ) if user_input is None or (
                    CONF_OPTION_DEVICES not in user_input and user_input[CONF_OPTION_DEVICES] is None) else vol.Schema(
            {
                vol.Required(CONF_OPTION_DEVICES, default=user_input[CONF_OPTION_DEVICES]): vol.In(
                    {user_input[CONF_OPTION_DEVICES]: user_input[CONF_OPTION_DEVICES]}),
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
                    return self.async_create_entry(title=DOMAIN, data={CONF_TARGET: list(
                        filter(lambda x: entity.original_name != x[CONF_ITEM_URL],
                               self.config_entry.options[CONF_TARGET]))})
                else:

                    return await self.async_step_entity(user_input={
                        CONF_OPTION_MODIFY: entity,
                    })

        option_entities = []
        entities = er.async_entries_for_config_entry(
            er.async_get(self.hass), self.config_entry.entry_id)
        hass = er.async_get(self.hass)

        for e in entities:
            entity = hass.async_get(e.entity_id)

            if CONF_OPTION_DEVICES in user_input and user_input[CONF_OPTION_DEVICES] is not None:
                for d in dr.async_entries_for_config_entry(dr.async_get(self.hass), self.config_entry.entry_id):
                    if d.serial_number != user_input[CONF_OPTION_DEVICES]:
                        continue

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
        _LOGGER.debug(user_input)
        if user_input is not None and CONF_OPTION_MODIFY in user_input:
            item = findItem(self.config_entry.options.get(CONF_TARGET, []), CONF_ITEM_URL,
                            user_input[CONF_OPTION_MODIFY].original_name)

            if item is None:
                raise ("Not found")

            if CONF_OPTION_DEVICES in user_input:
                if CONF_DEVICE not in item or item[CONF_DEVICE] != user_input[CONF_OPTION_DEVICES]:
                    raise ("Not found")

            return self.async_show_form(step_id="entity", data_schema=vol.Schema({
                vol.Required(CONF_ITEM_URL, default=item[CONF_ITEM_URL]): cv.string,
                vol.Optional(CONF_ITEM_MANAGEMENT_CATEGORY,
                             default=findValueOrDefault(item, CONF_ITEM_MANAGEMENT_CATEGORY, '')): cv.string,
                vol.Optional(CONF_ITEM_UNIT_TYPE,
                             default=findValueOrDefault(item, CONF_ITEM_UNIT_TYPE, 'piece')): vol.In(
                    CONF_ITEM_UNIT_TYPE_KIND),
                vol.Optional(CONF_ITEM_UNIT_PRICE,
                             default=findValueOrDefault(item, CONF_ITEM_UNIT_PRICE, 0)): cv.positive_int,
                vol.Optional(CONF_ITEM_UNIT, default=findValueOrDefault(item, CONF_ITEM_UNIT, 1)): cv.positive_int,
                vol.Required(CONF_ITEM_REFRESH_INTERVAL,
                             default=findValueOrDefault(item, CONF_ITEM_REFRESH_INTERVAL, 10)): cv.positive_int,
                vol.Required(CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR, default=24): cv.positive_int,
            }), errors={})

        if user_input is not None and CONF_ITEM_URL in user_input:
            data = deepcopy(self.config_entry.options.get(CONF_TARGET, []))
            for item in data[:]:
                if item[CONF_ITEM_URL] == user_input[CONF_ITEM_URL]:
                    if CONF_OPTION_DEVICES in user_input:
                        if CONF_DEVICE in item and item[CONF_DEVICE] == user_input[CONF_OPTION_DEVICES]:
                            data.remove(item)
                    else:
                        data.remove(item)

            data.append({
                CONF_DEVICE: user_input[CONF_OPTION_DEVICES] if CONF_OPTION_DEVICES in user_input else None,
                CONF_ITEM_URL: user_input[CONF_ITEM_URL],
                CONF_ITEM_MANAGEMENT_CATEGORY: user_input[
                    CONF_ITEM_MANAGEMENT_CATEGORY] if CONF_ITEM_MANAGEMENT_CATEGORY in user_input else None,
                CONF_ITEM_UNIT_TYPE: user_input[CONF_ITEM_UNIT_TYPE] if CONF_ITEM_UNIT_TYPE in user_input else 'piece',
                CONF_ITEM_UNIT_PRICE: user_input[CONF_ITEM_UNIT_PRICE] if CONF_ITEM_UNIT_PRICE in user_input and
                                                                          user_input[CONF_ITEM_UNIT_PRICE] != 0 else 0,
                CONF_ITEM_UNIT: user_input[CONF_ITEM_UNIT] if CONF_ITEM_UNIT in user_input and user_input[
                    CONF_ITEM_UNIT] != 0 else 0,
                CONF_ITEM_REFRESH_INTERVAL: user_input[CONF_ITEM_REFRESH_INTERVAL],
                CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR: user_input[
                    CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR] if CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR in user_input and
                                                             user_input[
                                                                 CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR] >= 1 else 24,
            })
            return self.async_create_entry(title=DOMAIN, data={CONF_TARGET: data})

        if CONF_OPTION_DEVICES in user_input and user_input[CONF_OPTION_DEVICES] is not None:
            return self.async_show_form(step_id="entity", data_schema=vol.Schema({
                vol.Required(CONF_OPTION_DEVICES, default=user_input[CONF_OPTION_DEVICES]): vol.In(
                    {user_input[CONF_OPTION_DEVICES]: user_input[CONF_OPTION_DEVICES]}),
                vol.Required(CONF_ITEM_URL, default=None): cv.string,
                vol.Optional(CONF_ITEM_MANAGEMENT_CATEGORY, default=''): cv.string,
                vol.Optional(CONF_ITEM_UNIT_TYPE, default='piece'): vol.In(CONF_ITEM_UNIT_TYPE_KIND),
                vol.Optional(CONF_ITEM_UNIT_PRICE, default=0): cv.positive_int,
                vol.Optional(CONF_ITEM_UNIT, default=1): cv.positive_int,
                vol.Required(CONF_ITEM_REFRESH_INTERVAL, default=10): cv.positive_int,
                vol.Required(CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR, default=24): cv.positive_int,
            }), errors={})
        else:
            return self.async_show_form(step_id="entity", data_schema=vol.Schema({
                vol.Required(CONF_ITEM_URL, default=None): cv.string,
                vol.Optional(CONF_ITEM_MANAGEMENT_CATEGORY, default=''): cv.string,
                vol.Optional(CONF_ITEM_UNIT_TYPE, default='piece'): vol.In(CONF_ITEM_UNIT_TYPE_KIND),
                vol.Optional(CONF_ITEM_UNIT_PRICE, default=0): cv.positive_int,
                vol.Optional(CONF_ITEM_UNIT, default=1): cv.positive_int,
                vol.Required(CONF_ITEM_REFRESH_INTERVAL, default=10): cv.positive_int,
                vol.Required(CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR, default=24): cv.positive_int,
            }), errors={})
