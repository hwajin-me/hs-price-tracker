from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from custom_components.price_tracker.const import (
    DEVICE_ENTITY_ID_FORMAT,
    DOMAIN,
    VERSION,
)


class Device(Entity):
    def __init__(self, device_type: str, device_id: str):
        self._device_id = device_id
        self._device_type = device_type
        self.entity_id = DEVICE_ENTITY_ID_FORMAT.format(
            "{}_{}".format(self._device_type, self._device_id)
        )

    @property
    def device_id(self):
        return self._device_id

    @property
    def unique_id(self):
        return self.entity_id

    @property
    def name(self):
        return self._device_id

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.entity_id)},
            name=self._device_id,
            manufacturer=self._device_type,
            model="Price Tracker Device",
            sw_version=VERSION,
            serial_number=self._device_id,
        )
