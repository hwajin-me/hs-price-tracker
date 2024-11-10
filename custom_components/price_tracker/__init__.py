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
from custom_components.price_tracker.const import DOMAIN, PLATFORMS
from custom_components.price_tracker.services.factory import create_service_item_url_parser, \
    create_service_item_target_parser
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

    # For upgrade options (1.0.0)
    if entry.options is not None \
            and 'target' in entry.options \
            and len(entry.options['target']) > 0:
        """Update"""
        options = {
            **entry.options,
            'target': Lu.map(entry.options['target'], lambda x: {**x, 'item_device_id': Lu.get(x, 'device')}),
        }
        options = {
            **options,
            'target': Lu.map(options['target'], lambda x: {**x, 'item_unique_id': IdGenerator.generate_entity_id(
                service_type=entry.data['type'],
                entity_target=create_service_item_target_parser(entry.data['type'])(create_service_item_url_parser(entry.data['type'])(x['item_url'])),
                device_id=Lu.get(x, 'item_device_id'),
            )}),
        }

        hass.config_entries.async_update_entry(entry=entry, data=entry.data, options=options)

    data = dict(entry.data)
    listeners = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id] = data

    entry.async_on_unload(listeners)

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    for e in entities:
        entity_registry.async_remove(e.entity_id)

    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(
        device_registry, entry.entry_id)

    for d in devices:
        device_registry.async_update_device(
            d.id, remove_config_entry_id=entry.entry_id)

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
