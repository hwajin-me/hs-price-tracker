from abc import abstractmethod
from datetime import datetime

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.consts.defaults import DOMAIN, VERSION


class PriceTrackerDevice(Entity):
    _name: str | None = None
    _proxies: list[str]

    def __init__(
        self,
        entry_id: str,
        device_type: str,
        device_id: str,
        proxies: str | list[str] | None = None,
    ):
        self._entry_id = entry_id
        self._device_id = str(device_id)
        self._device_type = device_type
        self._generate_device_id = IdGenerator.generate_device_id(self._device_id)
        self._attr_available = True
        self._updated_at: datetime | None = None
        if isinstance(proxies, str):
            self._proxies = [proxies]
        elif isinstance(proxies, list):
            self._proxies = proxies
        else:
            self._proxies = []
        self.entity_id = self._generate_device_id

    @property
    def proxies(self):
        return self._proxies

    @property
    def device_id(self):
        return self._device_id

    @property
    def unique_id(self):
        return self.entity_id

    @property
    def name(self):
        if self._name:
            return self._name

        return self._device_id

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.entity_id)},
            name=self.name,
            manufacturer=self._device_type,
            model="E-Commerce Integrator Device",
            sw_version=VERSION,
            serial_number=self._device_id,
        )

    @staticmethod
    def device_code() -> str:
        pass

    @staticmethod
    def device_name() -> str:
        pass


class CommerceDevice(Entity):
    def __init__(self, entry_id: str):
        """"""
        self._entry_id = entry_id

    @abstractmethod
    def add_to_cart(self, **kwargs):
        pass

    @abstractmethod
    def delete_from_cart(self, **kwargs):
        pass

    @abstractmethod
    def get_cart(self, **kwargs):
        pass

    @abstractmethod
    def get_order(self, **kwargs):
        pass

    @abstractmethod
    def get_orders(self, **kwargs):
        pass

    @abstractmethod
    def order(self, **kwargs):
        pass
