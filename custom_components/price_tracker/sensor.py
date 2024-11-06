import logging

from homeassistant import config_entries, core

from custom_components.price_tracker.engine.data import ItemUnitData, ItemUnitType
from custom_components.price_tracker.engine.device import createDevice
from custom_components.price_tracker.engine.sensor import PriceTrackerSensor
from custom_components.price_tracker.utils import findValueOrDefault
from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    hass.data[DOMAIN]["listener"] = []
    config = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug('sensor listen {} {}'.format(config, config_entry.options))

    if config_entry.options:
        config.update(config_entry.options)

    if CONF_DEVICE in config:
        device = createDevice(
            type=config[CONF_TYPE],
            attributes=config[CONF_DEVICE]
        )
    else:
        device = None

    sensors = []
    for target in config[CONF_TARGET]:
        try:
            sensor = PriceTrackerSensor(
                hass=hass,
                device=device,
                type=config[CONF_TYPE],
                item_url=target[CONF_ITEM_URL],
                refresh=target[CONF_ITEM_REFRESH_INTERVAL],
                management_category=findValueOrDefault(target, CONF_ITEM_MANAGEMENT_CATEGORY),
                price_change_period=findValueOrDefault(target, CONF_ITEM_PRICE_CHANGE_INTERVAL_HOUR, 24),
                unit=ItemUnitData(
                    price=float(target[CONF_ITEM_UNIT_PRICE]),
                    unit=target[CONF_ITEM_UNIT],
                    unit_type=ItemUnitType.of(target[CONF_ITEM_UNIT_TYPE])
                ) if CONF_ITEM_UNIT_PRICE in target and CONF_ITEM_UNIT in target and CONF_ITEM_UNIT_TYPE in target
                     and target[CONF_ITEM_UNIT_PRICE] and target[CONF_ITEM_UNIT] and target[CONF_ITEM_UNIT_TYPE]
                     and target[CONF_ITEM_UNIT_PRICE] != 0.0 and target[CONF_ITEM_UNIT] != 0.0
                else None
            )
            sensors.append(sensor)
        except Exception as e:
            hass.data[DOMAIN][config_entry.entry_id][CONF_TARGET].remove(target)
            raise e

    if device is not None:
        sensors.append(device)

    async_add_entities(sensors, update_before_add=True)


async def update_listener(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
