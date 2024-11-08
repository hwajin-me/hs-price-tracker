from homeassistant.components.sensor import SensorEntity

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.datas.item import ItemData


class PriceTrackerSensor(SensorEntity):
    _engine: PriceEngine
    _item_data: ItemData

    def __init__(self, engine: PriceEngine):
        """Initialize the sensor."""
        self._engine = engine

    @property
    def extra_state_attributes(self):
        if self._item_data is None:
            return {}

        return {
            **self._item_data.dict
        }
