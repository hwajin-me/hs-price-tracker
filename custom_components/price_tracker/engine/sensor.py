import asyncio
from threading import Timer

from homeassistant.helpers.entity import Entity

from custom_components.price_tracker.const import ENTITY_ID_FORMAT
from custom_components.price_tracker.engine.coupang import CoupangEngine
from custom_components.price_tracker.engine.data import ItemData
from custom_components.price_tracker.engine.engine import PriceEngine
from custom_components.price_tracker.engine.idus import IdusEngine
from custom_components.price_tracker.engine.kurly import KurlyEngine
from custom_components.price_tracker.engine.naver_smartstore import SmartstoreEngine
from custom_components.price_tracker.engine.ncnc import NcncEngine
from custom_components.price_tracker.engine.oliveyoung import OliveyoungEngine
from custom_components.price_tracker.engine.ssg import SsgEngine
from custom_components.price_tracker.exception import UnsupportedError


class PriceTrackerSensor(Entity):
    _engine: PriceEngine
    _attr_has_entity_name = True
    _data: ItemData = None

    def __init__(self, hass, type: str, item_url: str, refresh: int, management_category: str = None, ):
        super().__init__()

        self.hass = hass

        if type == 'coupang':
            self._engine = CoupangEngine(item_url)
        elif type == 'ssg':
            self._engine = SsgEngine(item_url)
        elif type == 'smartstore':
            self._engine = SmartstoreEngine(item_url)
        elif type == 'kurly':
            self._engine = KurlyEngine(item_url)
        elif type == 'ncnc':
            self._engine = NcncEngine(item_url)
        elif type == 'oliveyoung':
            self._engine = OliveyoungEngine(item_url)
        elif type == 'idus':
            self._engine = IdusEngine(item_url)
        else:
            raise UnsupportedError("Unsupported e-commerce type: {}".format(type))

        self._type = type
        self._item_url = item_url
        self._id = self._engine.id()
        self._loop = asyncio.get_event_loop()
        self._refresh_period = refresh * 60

        self.entity_id = ENTITY_ID_FORMAT.format(self._type, self._id)

        Timer(1, self.refreshTimer).start()

    def refreshTimer(self):
        self._loop.create_task(self.load())
        Timer(self._refresh_period, self.refreshTimer).start()

    async def load(self):
        self._data = await self._engine.load()

    @property
    def unique_id(self):
        return 'sensor.price_tracker_{}_{}'.format(self._type, self._id)

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
        return self._item_url

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._data is None:
            return None

        return self._data.price

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if self._data is None:
            return False

        return True

    @property
    def extra_state_attributes(self):
        if self._data is None:
            return None

        data = {
            'id': self._data.id,
            'price': self._data.price,
            'name': self._data.name,
            'description': self._data.description,
            'display_category': self._data.category,
            'inventory': self._data.inventory.value,
            'currency': self._data.currency,
            'url': self._data.url,
            'image': self._data.image
        }

        if self._data.unit is not None:
            data['unit_type'] = self._data.unit.unit_type.value
            data['unit_price'] = self._data.unit.price
            data['unit_value'] = self._data.unit.unit

        if self._data.delivery is not None:
            data['delivery'] = {
                'price': self._data.delivery.price,
                'type': self._data.delivery.type.value
            }

        return data

    def update(self):
        """Update the state."""
