import logging

from homeassistant import config_entries, core

from custom_components.price_tracker.engine.sensor import PriceTrackerSensor
from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    hass.data[DOMAIN]["listener"] = []
    config = hass.data[DOMAIN][config_entry.entry_id]

    if config_entry.options:
        config.update(config_entry.options)

    sensors = []
    for target in config[CONF_TARGET]:
        try:
            sensor = PriceTrackerSensor(
                hass,
                config[CONF_TYPE],
                target[CONF_ITEM_URL],
                target[CONF_ITEM_REFRESH_INTERVAL]
            )
            sensors.append(sensor)
        except Exception as e:
            hass.data[DOMAIN][config_entry.entry_id][CONF_TARGET].remove(target)
            raise e

    async_add_entities(sensors, update_before_add=True)
