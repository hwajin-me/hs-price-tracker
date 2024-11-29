from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.homeplus.const import CODE, NAME


class HomeplusSetup(PriceTrackerSetup):
    """Homeplus setup class."""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME
