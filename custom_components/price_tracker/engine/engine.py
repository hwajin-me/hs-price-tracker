from custom_components.price_tracker.device import Device
from custom_components.price_tracker.engine.data import ItemData


class PriceEngine:

    async def load(self) -> ItemData:
        """Load"""
        pass

    def id(self) -> str:
        pass

    @staticmethod
    def getId(item_url: str):
        pass
