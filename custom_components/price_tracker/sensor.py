import logging

from homeassistant import config_entries, core

from .components.sensor import PriceTrackerSensor
from .consts.confs import (
    CONF_ITEM_DEVICE_ID,
    CONF_DEVICE,
    CONF_TARGET,
    CONF_TYPE,
    CONF_ITEM_URL,
    CONF_ITEM_UNIT_TYPE,
    CONF_ITEM_UNIT,
    CONF_ITEM_REFRESH_INTERVAL,
    CONF_ITEM_MANAGEMENT_CATEGORY,
    CONF_PROXY,
)
from .consts.defaults import DOMAIN
from .datas.unit import ItemUnitType
from .services.factory import create_service_device_generator, create_service_engine
from .utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    config = hass.data[DOMAIN][config_entry.entry_id]
    type = config[CONF_TYPE]

    if config_entry.options:
        config.update(config_entry.options)

    devices = {}
    sensors = []
    proxy = Lu.get_or_default(config, CONF_PROXY, None)

    if CONF_DEVICE in config:
        for device in config[CONF_DEVICE]:
            # Get device generator
            device_generator = create_service_device_generator(type)
            if device_generator:
                target_device = device_generator(
                    {
                        **device,
                        "entry_id": config_entry.entry_id,
                    }
                )
                devices = {**devices, **{target_device.device_id: target_device}}
    async_add_entities(list(devices.values()), update_before_add=True)

    for target in Lu.get_or_default(config, CONF_TARGET, []):
        try:
            if CONF_ITEM_DEVICE_ID in target and target[CONF_ITEM_DEVICE_ID] in devices:
                device = devices[target[CONF_ITEM_DEVICE_ID]]
            else:
                device = None

            sensor = PriceTrackerSensor(
                engine=create_service_engine(type)(
                    item_url=target[CONF_ITEM_URL], proxy=proxy, device=device
                ),
                device=device,
                unit_type=ItemUnitType.of(target[CONF_ITEM_UNIT_TYPE])
                if CONF_ITEM_UNIT_TYPE in target
                and target[CONF_ITEM_UNIT_TYPE] != "auto"
                else ItemUnitType.PIECE,
                unit_value=Lu.get(target, CONF_ITEM_UNIT, 1)
                if CONF_ITEM_UNIT_TYPE in target
                and target[CONF_ITEM_UNIT_TYPE] != "auto"
                else 1,
                refresh_period=Lu.get(target, CONF_ITEM_REFRESH_INTERVAL, 30),
                management_category=Lu.get(target, CONF_ITEM_MANAGEMENT_CATEGORY, None),
            )

            sensors.append(sensor)

        except Exception as e:
            _LOGGER.exception("Device configuration error {}".format(e), e)

    async_add_entities(sensors, update_before_add=True)


async def update_listener(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
