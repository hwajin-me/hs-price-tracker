import logging
from abc import abstractmethod

from custom_components.price_tracker.services.data import ItemData


_LOGGER = logging.getLogger(__name__)
class PriceEngine:

    item_url: str
    id: any

    @abstractmethod
    async def load(self) -> ItemData:
        """Load"""
        pass

    @abstractmethod
    def id(self) -> str:
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
            return '_'.join(list(value.values()))
        elif value is str:
            return value
        elif isinstance(value, list):
            return '_'.join(value)
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

    @abstractmethod
    def url(self) -> str:
        """Get Item URL (redirect)"""
        pass
