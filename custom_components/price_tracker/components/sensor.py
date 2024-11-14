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
from custom_components.price_tracker.datas.price import (
    ItemPriceChangeData,
    create_item_price_change,
)
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType

_LOGGER = logging.getLogger(__name__)


class PriceTrackerSensor(RestoreEntity):
    _engine: PriceEngine
    _item_data: ItemData | None = None
    _item_data_previous: ItemData | None = None
    _management_category: str | None = None
    _price_change: ItemPriceChangeData | None = None
    _updated_at: datetime | None = None
    _refresh_period: int = 30  # minutes

    def __init__(
        self,
        engine: PriceEngine,
        device: PriceTrackerDevice | None = None,
        unit_type: ItemUnitType = ItemUnitType.PIECE,
        unit_value: int = 1,
        refresh_period: int = None,
        management_category: str = None,
    ):
        """Initialize the sensor."""
        self._engine = engine
        self._attr_unique_id = IdGenerator.generate_entity_id(
            self._engine.engine_code(),
            self._engine.entity_id,
            device.device_id if device is not None else None,
        )
        self.entity_id = self._attr_unique_id
        self._attr_entity_picture = None
        self._attr_name = self._attr_unique_id
        self._attr_unit_of_measurement = ""
        self._attr_state = STATE_UNKNOWN
        self._attr_available = False
        self._attr_icon = "mdi:cart"
        self._attr_device_class = "price"
        self._attr_device_info = device.device_info if device is not None else None
        self._attr_should_poll = True

        # Custom
        self._unit_type = unit_type
        self._unit_value = unit_value
        self._refresh_period = refresh_period if refresh_period is not None else 30
        self._updated_at = None
        self._management_category = management_category

    async def async_update(self):
        # Check last updated at
        if self._updated_at is not None or self._attr_available is False:
            if (
                self._updated_at is not None
                and (self._updated_at + timedelta(minutes=self._refresh_period))
                > datetime.now()
            ):
                _LOGGER.debug(
                    "Skip update cause refresh period. {} -({} / {}).".format(
                        self._attr_unique_id, self._updated_at, self._refresh_period
                    )
                )
                return None
        else:
            self._updated_at = datetime.now()

        try:
            data = await self._engine.load()

            if data is None:
                raise DataFetchErrorCauseEmpty("Data is empty")

            self._item_data_previous = self._item_data
            self._item_data = data
            self._price_change = create_item_price_change(
                updated_at=self._updated_at,
                period_hour=self._refresh_period,
                after_price=self._item_data.price.price,
                before_change_data=self._price_change,
                before_price=self._item_data_previous.price.price
                if self._item_data_previous is not None
                else None,
            )

            # Calculate unit
            unit = (
                ItemUnitData(
                    price=self._item_data.price.price,
                    unit_type=self._unit_type,
                    unit=self._unit_value,
                )
                if self._item_data.unit.is_basic
                else self._item_data.unit
            )

            self._attr_extra_state_attributes = {
                **self._item_data.dict,
                **unit.dict,
                "price_change_status": self._price_change.status.name,
                "price_change_before_price": self._price_change.before_price,
                "price_change_after_price": self._price_change.after_price,
                "management_category": self._management_category,
                "updated_at": self._updated_at,
                "refresh_period": self._refresh_period,
            }
            self._attr_name = self._item_data.name
            self._attr_state = self._item_data.price.price
            self._attr_entity_picture = self._item_data.image
            self._attr_available = True
            self._attr_unit_of_measurement = self._item_data.price.currency
        except Exception as e:
            self._attr_available = False
            self._attr_state = STATE_UNKNOWN
            self._attr_extra_state_attributes = {}
            _LOGGER.exception("Error while updating the sensor: %s", e)

    async def async_added_to_hass(self) -> None:
        try:
            """Handle entity which will be added."""
            await super().async_added_to_hass()
            state = await self.async_get_last_state()

            if not state:
                return

            if (
                "price_change_status" in state.attributes
                and "price_change_before_price" in state.attributes
                and "price_change_after_price" in state.attributes
            ):
                self._price_change = create_item_price_change(
                    updated_at=state.last_updated,
                    period_hour=self._refresh_period,
                    after_price=state.attributes["price_change_after_price"],
                    before_change_data=None,
                    before_price=state.attributes["price_change_before_price"],
                )

            self._attr_available = True

            await self.async_update()

            async_dispatcher_connect(
                self.hass, DATA_UPDATED, self._schedule_immediate_update
            )
        except Exception as e:
            _LOGGER.warning("Error while adding the sensor: %s", e)

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)
