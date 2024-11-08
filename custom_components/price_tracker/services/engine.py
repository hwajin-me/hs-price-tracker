from abc import abstractmethod
from custom_components.price_tracker.services.data import ItemData


class PriceEngine:

    @abstractmethod
    async def load(self) -> ItemData:
        """Load"""
        pass

    @abstractmethod
    def id(self) -> str:
        pass

    @staticmethod
    def parse_id(item_url: str):
        """Parse ID from URL"""
        pass

    @staticmethod
    def engine_code() -> str:
        """Engine code"""
        pass

    @staticmethod
    def engine_name() -> str:
        """Engine human readable name"""
        pass

    @abstractmethod
    def url(self) -> str:
        """Get Item URL (redirect)"""
        pass
