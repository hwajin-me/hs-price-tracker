import logging

from homeassistant import config_entries, core

from .components.sensor import PriceTrackerSensor
from .consts.confs import CONF_ITEM_DEVICE_ID, CONF_DEVICE, CONF_TARGET, CONF_TYPE, CONF_ITEM_URL
from .consts.defaults import DOMAIN
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

    if CONF_DEVICE in config:
        for device in config[CONF_DEVICE]:
            # Get device generator
            device_generator = create_service_device_generator(type)
            if device_generator:
                target_device = device_generator({
                    **device,
                    'entry_id': config_entry.entry_id,
                })
                devices = {
                    **devices,
                    **{
                        target_device.device_id: target_device
                    }
                }
    async_add_entities(list(devices.values()), update_before_add=True)

    for target in Lu.get_or_default(config, CONF_TARGET, []):
        try:
            if CONF_ITEM_DEVICE_ID in target \
                    and target[CONF_ITEM_DEVICE_ID] in devices:
                device = devices[target[CONF_ITEM_DEVICE_ID]]
            else:
                device = None

            sensor = PriceTrackerSensor(
                engine=create_service_engine(type)(target[CONF_ITEM_URL] if device is None else {
                    'item_url': target[CONF_ITEM_URL],
                    'device': device
                }),
                device=device,
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
