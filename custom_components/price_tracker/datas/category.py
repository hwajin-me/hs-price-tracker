class ItemCategoryData:

    def __init__(self, category: any):
        if isinstance(category, list):
            self._category = '|'.join(category).strip()
        else:
            self._category = str(category.replace(">", "|").strip())

    @property
    def split(self):
        return self._category.split('|')
