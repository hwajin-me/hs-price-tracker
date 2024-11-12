from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.smartstore.const import CODE, NAME


class SmartstoreSetup(PriceTrackerSetup):
    """"""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME
