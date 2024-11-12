from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.oliveyoung.const import CODE, NAME


class OliveyoungSetup(PriceTrackerSetup):
    """"""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME
