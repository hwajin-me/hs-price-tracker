import re

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.services.dawn_market.const import NAME, CODE


class DawnMarketEngine(PriceEngine):
    @staticmethod
    def parse_id(item_url: str) -> any:
        match = re.search(r"goods-info/(?P<id>\w+)", item_url)

        if match:
            return match.group("id")

    @staticmethod
    def engine_name() -> str:
        return NAME

    @staticmethod
    def engine_code() -> str:
        return CODE
