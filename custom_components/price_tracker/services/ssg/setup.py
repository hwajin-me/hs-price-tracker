from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.ssg.const import CODE


class SsgSetup(PriceTrackerSetup):
    """"""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return "SSG (E-Mart, Korea)"
