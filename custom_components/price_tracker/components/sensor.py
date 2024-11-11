import logging
from datetime import datetime, timedelta

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.price_tracker.components.device import PriceTrackerDevice
from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import DataFetchErrorCauseEmpty
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.consts.defaults import DATA_UPDATED
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.datas.price import ItemPriceChangeData, ItemPriceChangeStatus
from custom_components.price_tracker.datas.unit import ItemUnitData

_LOGGER = logging.getLogger(__name__)


class PriceTrackerSensor(RestoreEntity):
    _engine: PriceEngine
    _item_data: ItemData | None = None
    _item_data_previous: ItemData | None = None
    _management_category: str | None = None
    _unit: ItemUnitData = ItemUnitData(price=0.0)
    _price_change: ItemPriceChangeData = ItemPriceChangeData(status=ItemPriceChangeStatus.NO_CHANGE)
    _updated_at: datetime | None = None
    _refresh_period: int = 30  # minutes

    def __init__(self, engine: PriceEngine, device: PriceTrackerDevice | None = None):
        """Initialize the sensor."""
        self._engine = engine
        self._attr_unique_id = IdGenerator.generate_entity_id(self._engine.engine_code(), self._engine.entity_id,
                                                              device.device_id if device is not None else None)
        self.entity_id = self._attr_unique_id
        self._attr_entity_picture = None
        self._attr_name = self._attr_unique_id
        self._attr_unit_of_measurement = ''
        self._attr_state = STATE_UNKNOWN
        self._attr_available = False
        self._attr_icon = 'mdi:cart'
        self._attr_device_class = 'price'
        self._attr_device_info = device.device_info if device is not None else None
        self._attr_should_poll = True
        self._updated_at = None

    async def async_update(self):
        # Check last updated at
        if self._updated_at is not None:
            if (
                    self._updated_at + timedelta(minutes=self._refresh_period)
            ) > datetime.now():
                _LOGGER.debug(
                    "Skip update cause refresh period. {} -({} / {}).".format(
                        self._attr_unique_id, self._updated_at, self._refresh_period
                    )
                )
                return None

        try:
            data = await self._engine.load()

            if data is None:
                raise DataFetchErrorCauseEmpty('Data is empty')

            self._item_data_previous = self._item_data
            self._item_data = data
            self._price_change = ItemPriceChangeData(
                status=ItemPriceChangeStatus.NO_CHANGE if self._item_data_previous is None else ItemPriceChangeStatus.INCREMENT_PRICE if self._item_data.price > self._item_data_previous.price else ItemPriceChangeStatus.DECREMENT_PRICE,
                before_price=self._item_data_previous.price if self._item_data_previous is not None else 0.0,
                after_price=self._item_data.price,
            ) if self._item_data is not None and self._item_data_previous else ItemPriceChangeData(
                status=ItemPriceChangeStatus.NO_CHANGE)
            self._updated_at = datetime.now()
            self._attr_extra_state_attributes = {
                **self._item_data.dict,
                'management_category': self._management_category,
                'updated_at': self._updated_at,
                'price_change': self._price_change.dict,
                'refresh_period': self._refresh_period,
            }
            self._attr_name = self._item_data.name
            self._attr_state = self._item_data.price
            self._attr_entity_picture = self._item_data.image
            self._attr_available = True
            self._attr_unit_of_measurement = self._item_data.currency
        except Exception as e:
            self._attr_available = False
            self._attr_state = STATE_UNKNOWN
            self._attr_extra_state_attributes = {}
            _LOGGER.exception("Error while updating the sensor: %s", e)

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state:
            return
        self._state = state.state

        _LOGGER.debug('Restoring state from previous version, {} >>>>> {}'.format(state, state.attributes))

        # ADDED CODE HERE
        # self._attr_unique_id = state.attributes['unique_id']

            # self.attrs = {
            #     'expiration_date': datetime.strptime(
            #         state.attributes['expiration_date'], '%Y-%m-%dT%H:%M:%S'),
            #     'expired': state.attributes['expired'],
            #     'purchased': state.attributes['purchased'],
            #     'remaining': state.attributes['remaining'],
            # }

        async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)
