from custom_components.price_tracker.components.setup import PriceTrackerSetup
from custom_components.price_tracker.services.idea_nutrition.const import CODE, NAME


class IdeaNutritionSetup(PriceTrackerSetup):
    """Homeplus setup class."""

    @staticmethod
    def setup_code() -> str:
        return CODE

    @staticmethod
    def setup_name() -> str:
        return NAME
