import logging
from datetime import timedelta, datetime

from homeassistant.components.sensor import SensorEntity

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import UnsupportedError
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.device import Device
from custom_components.price_tracker.services.coupang.engine import CoupangEngine
from custom_components.price_tracker.services.data import (
    ItemPriceChangeStatus,
    ItemData,
    ItemUnitData,
)
from custom_components.price_tracker.services.gsthefresh.engine import GsTheFreshEngine
from custom_components.price_tracker.services.idus.engine import IdusEngine
from custom_components.price_tracker.services.kurly.engine import KurlyEngine
from custom_components.price_tracker.services.smartstore.engine import SmartstoreEngine
from custom_components.price_tracker.services.ncnc.engine import NcncEngine
from custom_components.price_tracker.services.oasis.engine import OasisEngine
from custom_components.price_tracker.services.oliveyoung.engine import OliveyoungEngine
from custom_components.price_tracker.services.ssg.engine import SsgEngine

_LOGGER = logging.getLogger(__name__)


class PriceTrackerSensor(SensorEntity):
    _engine: PriceEngine
    _attr_has_entity_name = True
    _data: ItemData = None
    _data_previous: ItemData = None
    _price_change_status: ItemPriceChangeStatus = ItemPriceChangeStatus.NO_CHANGE
    _price_changed_at: datetime = None
    _price_change_period: int = 24
    _price_change_amount: float = 0.0
    _updated_at: datetime = None
    _unit: ItemUnitData = None
    _management_category: str = None

    def __init__(
        self,
        hass,
        type: str,
        item_url: str,
        refresh: int,
        device: Device = None,
        management_category: str = None,
        price_change_period: int = 24,
        unit: ItemUnitData = None,
    ):
        super().__init__()
        self._attr_device_info = device.device_info if device is not None else None
        self.hass = hass

        if type == "coupang":
            self._engine = CoupangEngine(item_url)
        elif type == "ssg":
            self._engine = SsgEngine(item_url)
        elif type == "smartstore":
            self._engine = SmartstoreEngine(item_url)
        elif type == "kurly":
            self._engine = KurlyEngine(item_url)
        elif type == "ncnc":
            self._engine = NcncEngine(item_url)
        elif type == "oliveyoung":
            self._engine = OliveyoungEngine(item_url)
        elif type == "oasis":
            self._engine = OasisEngine(item_url)
        elif type == "idus":
            self._engine = IdusEngine(item_url)
        elif type == "gsthefresh":
            self._engine = GsTheFreshEngine(item_url=item_url, device=device)
        else:
            raise UnsupportedError('Unsupported e-commerce type "{}".'.format(type))

        self._type = type
        self._item_url = item_url
        self._id = self._engine.id
        self._refresh_period = refresh
        self._price_change_period = price_change_period
        self._unit = unit
        self._management_category = management_category
        self.entity_id = IdGenerator.generate_entity_id(
            service_type=self._type,
            device_id=self._engine.device_id,
            entity_target=self._engine.entity_id,
        )

    async def load(self):
        # Check last updated at
        if self._updated_at is not None:
            if (
                self._updated_at + timedelta(minutes=self._refresh_period)
            ) > datetime.now():
                _LOGGER.debug(
                    "Skip update cause refresh period. {} - {} ({} / {}).".format(
                        self._type, self._id, self._updated_at, self._refresh_period
                    )
                )
                return None

        try:
            if self._data is not None:
                self._data_previous = self._data
            self._data = await self._engine.load()

            if self._data is None:
                return

            self._updated_at = datetime.now()
            if (
                self._data_previous is not None
                and self._data.total_price != self._data_previous.total_price
                and (
                    self._price_changed_at is None
                    or (
                        self._price_changed_at
                        < datetime.now() + timedelta(hours=self._price_change_period)
                    )
                )
            ):
                self._price_change_status = (
                    ItemPriceChangeStatus.INC_PRICE
                    if self._data.total_price > self._data_previous.total_price
                    else ItemPriceChangeStatus.DEC_PRICE
                )
                self._price_changed_at = datetime.now()
                self._price_change_amount = (
                    self._data.total_price - self._data_previous.total_price
                )
            elif self._data_previous is None:
                self._price_change_status = ItemPriceChangeStatus.NO_CHANGE
                self._price_changed_at = datetime.now()
                self._price_change_amount = 0.0
        except Exception as e:
            _LOGGER.error("Error occurred while loading data. {}".format(e))
            self._data = None

    @property
    def unique_id(self):
        return self.entity_id

    @property
    def entity_picture(self):
        if self._data is None:
            return None

        return self._data.image

    @property
    def unit_of_measurement(self):
        if self._data is None:
            return None

        return self._data.currency

    @property
    def icon(self):
        return "mdi:cart"

    @property
    def name(self):
        if self._data is None:
            return self._id

        return self._data.name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._data is None:
            return None

        return self._data.price

    @property
    def available(self) -> bool:
        if self._data is None:
            return False

        return True

    @property
    def extra_state_attributes(self):
        if self._data is None:
            return None

        data = {
            "id": self._data.id,
            "price": self._data.price,
            "original_price": self._data.original_price,
            "name": self._data.name,
            "description": self._data.description,
            "display_category": self._data.category,
            "inventory": self._data.inventory.value,
            "currency": self._data.currency,
            "url": self._data.url,
            "image": self._data.image,
            "price_change_status": self._price_change_status,
            "price_changed_at": self._price_changed_at,
        }

        if self._unit is not None:
            data["unit_type"] = self._unit.unit_type.value
            data["unit_price"] = self._unit.price
            data["unit_value"] = self._unit.unit
        elif self._data.unit is not None:
            data["unit_type"] = self._data.unit.unit_type.value
            data["unit_price"] = self._data.unit.price
            data["unit_value"] = self._data.unit.unit

        if self._data.delivery is not None:
            data["delivery"] = {
                "price": self._data.delivery.price,
                "type": self._data.delivery.type.value,
            }

        if self._data.options is not None:
            data["item_options"] = []
            for option in self._data.options:
                data["item_options"].append(
                    {
                        "id": option.id,
                        "name": option.name,
                        "price": option.price,
                        "inventory": option.inventory,
                    }
                )

        return data

    async def async_update(self):
        await self.load()
