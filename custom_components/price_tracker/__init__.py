from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.consts.confs import (
    CONF_ITEM_DEVICE_ID,
    CONF_ITEM_UNIQUE_ID,
)
from custom_components.price_tracker.consts.defaults import DOMAIN, PLATFORMS
from custom_components.price_tracker.services.factory import (
    create_service_item_url_parser,
    create_service_item_target_parser,
    create_service_device_parser_and_parse,
    has_service_item_target_parser,
)
from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the price tracker component."""
    _LOGGER.debug("Setting up price tracker component {}".format(config))
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Setting up entry and data {} > {}".format(entry, entry.data))
    _LOGGER.debug("Setting up entry and options {} > {}".format(entry, entry.options))

    # For upgrade options (1.4.0)
    if not has_service_item_target_parser(entry.data["type"]):
        return False

    # For upgrade options (1.0.0)
    if entry.data is not None and "device" in entry.data:
        """Update device_id"""
        data = {
            **entry.data,
            "device": Lu.map(
                entry.data["device"],
                lambda x: {
                    **x,
                    CONF_ITEM_DEVICE_ID: IdGenerator.generate_device_id(
                        create_service_device_parser_and_parse(entry.data["type"], x)
                    )
                    if create_service_device_parser_and_parse(entry.data["type"], x)
                    is not None
                    else None,
                },
            ),
        }
    else:
        data = entry.data

    if entry.options is not None and "target" in entry.options:
        options = {
            **entry.options,
            "target": Lu.map(
                entry.options["target"],
                lambda x: {
                    **x,
                    CONF_ITEM_DEVICE_ID: Lu.get(x, "device")
                    if Lu.get(x, "device") is not None
                    else Lu.get(x, CONF_ITEM_DEVICE_ID),
                },
            ),
        }

        """Update item_url (item_unique_id)"""
        options = {
            **options,
            "target": Lu.map(
                options["target"],
                lambda x: {
                    **x,
                    CONF_ITEM_UNIQUE_ID: IdGenerator.generate_entity_id(
                        service_type=entry.data["type"],
                        entity_target=create_service_item_target_parser(
                            entry.data["type"]
                        )(
                            create_service_item_url_parser(entry.data["type"])(
                                x["item_url"]
                            )
                        ),
                        device_id=IdGenerator.get_device_target_from_id(
                            Lu.get(x, CONF_ITEM_DEVICE_ID)
                        )
                        if Lu.get(x, CONF_ITEM_DEVICE_ID) is not None
                        else None,
                    ),
                },
            ),
        }
    else:
        options = {"target": []}

    hass.config_entries.async_update_entry(entry=entry, data=data, options=options)

    data = dict(data)
    listeners = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id] = data

    entry.async_on_unload(listeners)

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    for e in entities:
        entity_registry.async_remove(e.entity_id)

    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    for d in devices:
        device_registry.async_update_device(d.id, remove_config_entry_id=entry.entry_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)
