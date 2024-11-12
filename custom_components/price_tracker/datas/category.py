import dataclasses


@dataclasses.dataclass
class ItemCategoryData:
    def __init__(self, category: any):
        if category is None:
            self._category = ""
        if isinstance(category, list):
            self._category = "|".join(category).strip()
        elif isinstance(category, str):
            self._category = str(category.replace(">", "|").strip())
        else:
            self._category = str(category).strip()

    @property
    def split(self):
        return self._category.split("|")
