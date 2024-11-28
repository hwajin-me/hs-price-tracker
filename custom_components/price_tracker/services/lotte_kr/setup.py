from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.lotte_kr.const import CODE, NAME


class LotteOnKoreaSetup(PriceTrackerSetup):
    """Setup for Lotte on Korea."""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME
