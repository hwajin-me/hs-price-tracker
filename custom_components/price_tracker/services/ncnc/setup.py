from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.ncnc.const import CODE


class NcncSetup(PriceTrackerSetup):
    """"""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return "니콘내콘 (Korea)"
