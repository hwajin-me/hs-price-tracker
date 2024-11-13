import dataclasses
from enum import Enum


class ItemUnitType(Enum):
    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    PIECE = "piece"

    @classmethod
    def list(cls) -> list:
        return list(map(lambda c: c.value, cls))

    @staticmethod
    def of(label):
        if str(label).lower() in ("g", "gram", "グラム", "그램", "克"):
            return ItemUnitType.G
        elif str(label).lower() in (
            "kg",
            "kilogram",
            "キログラム",
            "キロ",
            "킬로그램",
            "킬로",
        ):
            return ItemUnitType.KG
        elif str(label).lower() in (
            "ml",
            "millilitre",
            "ミリリットル",
            "ミリ",
            "밀리리터",
            "밀리",
        ):
            return ItemUnitType.ML
        elif str(label).lower() in ("l", "litre", "リットル", "리터"):
            return ItemUnitType.L
        else:
            return ItemUnitType.PIECE


@dataclasses.dataclass
class ItemUnitData:
    def __init__(
        self,
        price: float,
        unit_type: ItemUnitType = ItemUnitType.PIECE,
        unit: float = 1,
    ):
        self.unit_type = unit_type
        self.unit = unit
        self.price = price

        if unit_type == ItemUnitType.KG:
            self.unit_type = ItemUnitType.G
            self.price = price / 1000
        elif unit_type == ItemUnitType.L:
            self.unit_type = ItemUnitType.ML
            self.price = price / 1000
        resize = ItemUnitData._calculate(unit=self.unit, price=self.price)
        self.price = resize["price"]
        self.unit = resize["unit"]

    @property
    def is_basic(self):
        return self.unit == 1 and self.unit_type == ItemUnitType.PIECE

    @staticmethod
    def _calculate(unit: float, price: float):
        if unit <= 1:
            return {"unit": unit, "price": price}
        elif unit < 10:
            return ItemUnitData._calculate(unit - 1, (price / unit) * (unit - 1))

        return ItemUnitData._calculate(unit / 10, price / 10)

    @property
    def dict(self):
        return {
            "unit_type": self.unit_type.value,
            "unit_value": self.unit,
            "unit_price": self.price,
        }
