import logging
from abc import abstractmethod

from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


class PriceEngine:
    item_url: str
    id: any

    @abstractmethod
    async def load(self) -> ItemData | None:
        """Load"""
        pass

    @abstractmethod
    def id_str(self) -> str:
        pass

    @property
    def device_id(self) -> str | None:
        return None

    @property
    def entity_id(self) -> str:
        return self.target_id(self.id)

    @staticmethod
    def target_id(value: any) -> str:
        if isinstance(value, dict):
            items = Lu.filter(list(value.values()), lambda x: x is not None)
            return "_".join(items)
        elif value is str:
            return value
        elif isinstance(value, list):
            items = Lu.filter(value, lambda x: x is not None)
            return "_".join(items)
        else:
            return str(value)

    @staticmethod
    def parse_id(item_url: str) -> any:
        """Parse ID from URL"""
        pass

    @staticmethod
    def engine_code() -> str:
        """Engine code"""
        pass

    @staticmethod
    def engine_name() -> str:
        """Engine read-able name"""
        pass
