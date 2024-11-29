import dataclasses

from custom_components.price_tracker.utilities.list import Lu


@dataclasses.dataclass
class ItemCategoryData:
    def __init__(self, category: any):
        if category is None:
            self._category = ""
        if isinstance(category, list):
            target = Lu.filter(category, lambda x: x is not None and str(x) != "")
            self._category = "|".join(Lu.map(target, lambda x: str(x))).strip()
        elif isinstance(category, str):
            self._category = str(category.replace(">", "|").strip())
        else:
            self._category = str(category).strip()

    @property
    def split(self):
        return self._category.split("|")

    @property
    def last(self):
        if len(self.split) == 0:
            return None

        return self.split[-1]
