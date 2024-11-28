from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.iherb.const import CODE, NAME


class IherbSetup(PriceTrackerSetup):
    """iHerb setup class."""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME
