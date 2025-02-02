import logging
from datetime import datetime, timedelta

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.price_tracker.components.device import PriceTrackerDevice
from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.consts.defaults import DATA_UPDATED
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import (
    ItemPriceChangeData,
    create_item_price_change,
    ItemPriceChangeStatus,
    ItemPriceData,
)
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


class PriceTrackerSensor(RestoreEntity):
    # STATIC
    _attr_icon = "mdi:cart"
    _attr_device_class = "price"
    _attr_should_poll = True

    # Require
    _engine: PriceEngine
    _item_data: ItemData | None = None

    # Custom
    _management_category: str | None = None
    _price_change: ItemPriceChangeData = create_item_price_change(
        updated_at=datetime.now(),
        period_hour=30,
    )
    _refresh_period: int = 30  # minutes
    _unit_type: ItemUnitType = ItemUnitType.PIECE
    _unit_value: int = 1
    _updated_at: datetime | None = None

    def __init__(
        self,
        engine: PriceEngine,
        device: PriceTrackerDevice | None = None,
        unit_type: ItemUnitType = ItemUnitType.PIECE,
        unit_value: int = 1,
        refresh_period: int = 30,
        management_category: str = None,
        management_categories: str = None,
        debug: bool = False,
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
        self._attr_available = True
        self._attr_device_info = device.device_info if device is not None else None
        self._attr_extra_state_attributes = {
            "provider": self._engine.engine_code(),
        }

        # Custom
        if management_categories is not None:
            management_categories = Lu.map(
                management_categories.split(","), lambda x: str(x).strip()
            )
        if management_categories is None:
            management_categories = []

        self._unit_type = unit_type
        self._unit_value = unit_value
        self._refresh_period = refresh_period if refresh_period is not None else 30
        self._updated_at = datetime.now()
        self._management_category = management_category
        self._management_categories = management_categories
        self._debug = debug
        self._engine_status = True

    @property
    def engine_id_str(self):
        return self._engine.id_str()

    async def async_update(self):
        # Check last updated at
        if (
            self._engine_status
            and self._updated_at is not None
            and self._attr_available is True
        ):
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
                return True

        _LOGGER.debug(
            "Update sensor: %s (%s) - %s",
            self._attr_unique_id,
            self._updated_at,
            self._attr_available,
        )

        # Ignore deleted item
        if self._item_data is not None and self._item_data.status == ItemStatus.DELETED:
            self._attr_available = True
            self._update_updated_at()
            return True

        try:
            data = await self._engine.load()

            if data is None:
                if (
                    self._updated_at is None
                    or self._updated_at + timedelta(hours=6) < datetime.now()
                    or self._debug
                ):
                    self._attr_available = False
                    self._update_engine_status(False)
                else:
                    self._attr_available = True
                    self._update_engine_status(False)
                return True

            self._price_change = create_item_price_change(
                updated_at=datetime.now(),
                period_hour=self._refresh_period,
                after_price=data.price.price,
                before_price=self._item_data.price.price
                if self._item_data is not None
                else None,
            )
            self._item_data = data

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
                "management_categories": self._management_categories,
                "updated_at": self._updated_at,
                "refresh_period": self._refresh_period,
            }
            self._attr_name = self._item_data.name
            self._attr_state = self._item_data.price.price
            self._attr_entity_picture = self._item_data.image
            self._attr_available = True
            self._attr_unit_of_measurement = self._item_data.price.currency
            self._update_engine_status(True)
        except Exception as e:
            if (
                self._updated_at is None
                or self._updated_at + timedelta(hours=6) < datetime.now()
                or self._debug
            ):
                self._attr_available = False
                self._update_engine_status(False)
            else:
                self._attr_available = True
                self._update_engine_status(False)
        finally:
            self._update_updated_at()

    async def async_added_to_hass(self) -> None:
        try:
            """Handle entity which will be added."""
            await super().async_added_to_hass()
            state = await self.async_get_last_state()

            if self._item_data is not None:
                return

            if not state:
                self._attr_available = False
                await self.async_update()
                return

            if "updated_at" in state.attributes:
                self._updated_at = datetime.fromisoformat(
                    state.attributes["updated_at"]
                )
                self._attr_available = True
            else:
                self._update_engine_status(False)

            self._attr_name = Lu.get(state.attributes, "name")
            self._attr_state = Lu.get(state.attributes, "price")
            self._attr_entity_picture = Lu.get(state.attributes, "entity_picture")
            self._attr_unit_of_measurement = Lu.get(
                state.attributes, "unit_of_measurement"
            )
            self._attr_extra_state_attributes = {
                **self._attr_extra_state_attributes,
                **state.attributes,
                "management_category": self._management_category,
                "management_categories": self._management_categories,
            }

            if "product_id" in state.attributes:
                self._item_data = ItemData(
                    id=state.attributes["product_id"],
                    brand=Lu.get(state.attributes, "brand"),
                    name=state.attributes["name"],
                    price=ItemPriceData(
                        price=state.attributes["price"],
                        original_price=state.attributes["original_price"],
                        currency=state.attributes["unit_of_measurement"],
                        payback_price=state.attributes["payback_price"],
                    ),
                    unit=ItemUnitData(
                        unit_type=Lu.get(
                            state.attributes, "unit_type", ItemUnitType.PIECE.name
                        ),
                        unit=Lu.get(state.attributes, "unit_value", 1),
                        price=Lu.get(state.attributes, "unit_price"),
                    ),
                    image=state.attributes["entity_picture"],
                    description=Lu.get(state.attributes, "description"),
                    url=Lu.get(state.attributes, "url"),
                )
            else:
                self._attr_available = False

            # Update price change
            if (
                "price_change_status" in state.attributes
                and "price_change_before_price" in state.attributes
                and "price_change_after_price" in state.attributes
            ):
                self._price_change = ItemPriceChangeData(
                    status=ItemPriceChangeStatus.of(
                        Lu.get(state.attributes, "price_change_status", "no_change")
                    ),
                    before_price=Lu.get(state.attributes, "price_change_before_price"),
                    after_price=Lu.get(state.attributes, "price_change_after_price"),
                    updated_at=self._updated_at,
                )
                self._attr_extra_state_attributes = {
                    **self._attr_extra_state_attributes,
                    "price_change_status": self._price_change.status.name,
                    "price_change_before_price": self._price_change.before_price,
                    "price_change_after_price": self._price_change.after_price,
                }

            await self.async_update()

            async_dispatcher_connect(
                self.hass, DATA_UPDATED, self._schedule_immediate_update
            )
        except Exception as e:
            _LOGGER.warning("Error while adding the sensor: %s", e)

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

    def _update_updated_at(self):
        self._updated_at = datetime.now()
        self._attr_extra_state_attributes = {
            **self._attr_extra_state_attributes,
            "updated_at": self._updated_at,
        }

    def _update_engine_status(self, status: bool):
        if self._attr_extra_state_attributes is None:
            self._attr_extra_state_attributes = {}

        self._attr_extra_state_attributes = {
            **self._attr_extra_state_attributes,
            "engine_status": "FETCHED" if status else "ERROR",
        }
        self._engine_status = status
