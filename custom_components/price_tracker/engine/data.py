from enum import Enum


class ItemUnitType(Enum):
    G = 'g'
    KG = 'kg'
    ML = 'ml'
    L = 'l'
    PIECE = 'piece'

    @staticmethod
    def of(label):
        if str(label).lower() in ('g', 'gram', 'グラム', '그램'):
            return ItemUnitType.G
        elif str(label).lower() in ('kg', 'kilogram', 'キログラム', 'キロ', '킬로그램'):
            return ItemUnitType.KG
        elif str(label).lower() in ('ml', 'millilitre', 'ミリリットル', 'ミリ', '밀리리터', '밀리'):
            return ItemUnitType.ML
        elif str(label).lower() in ('l', 'litre', 'リットル', '리터'):
            return ItemUnitType.L
        else:
            return ItemUnitType.PIECE


class ItemPriceChangeStatus(Enum):
    INC_PRICE = 'increment_price',
    DEC_PRICE = 'decrement_price',
    NO_CHANGE = 'no_change'


class DeliveryPayType(Enum):
    FREE = 'free'
    PAID = 'paid'
    UNKNOWN = 'unknown'


class InventoryStatus(Enum):
    IN_STOCK = 'in_stock'
    ALMOST_SOLD_OUT = 'almost_sold_out'
    OUT_OF_STOCK = 'out_of_stock'


class BooleanType(Enum):
    BOOL_TRUE = True
    BOOL_FALSE = False

    @staticmethod
    def of(label):
        if label is None:
            return BooleanType.BOOL_FALSE

        if label:
            return BooleanType.BOOL_TRUE
        elif label == 1:
            return BooleanType.BOOL_TRUE
        elif not label:
            return BooleanType.BOOL_FALSE
        elif str(label).lower() in ('yes', 'y', 'はい', '예', 'ok', '1'):
            return BooleanType.BOOL_TRUE
        else:
            return BooleanType.BOOL_FALSE


class DeliveryData:
    def __init__(self, price: float, type: DeliveryPayType = DeliveryPayType.PAID):
        self.price = price
        self.type = type


class ItemUnitData:
    def __init__(self, price: float, unit_type: ItemUnitType = ItemUnitType.PIECE, unit: float = 1):
        self.unit_type = unit_type
        self.unit = unit
        self.price = price

        if unit_type == ItemUnitType.KG:
            self.unit_type = ItemUnitType.G
            self.price = price / 1000
        elif unit_type == ItemUnitType.L:
            self.unit_type = ItemUnitType.ML
            self.price = price / 1000
        resize = ItemUnitData.toOneQuantity(unit=self.unit, price=self.price)
        self.price = resize['price']
        self.unit = resize['unit']

    @staticmethod
    def toOneQuantity(unit: float, price: float):
        if unit <= 1:
            return {
                'unit': unit,
                'price': price
            }
        elif unit < 10:
            return ItemUnitData.toOneQuantity(unit - 1, (price / unit) * (unit - 1))

        return ItemUnitData.toOneQuantity(unit / 10, price / 10)


class ItemOptionData:
    def __init__(self, id: any, name: str, price: float):
        self.id = id
        self.name = name
        self.price = price


class ItemData:
    def __init__(
            self,
            id: any,
            price: float,
            name: str,
            original_price: float = None,
            description: str = None,
            category: str = None,
            delivery: DeliveryData = None,
            url: str = None,
            image: str = None,
            unit: ItemUnitData = None,
            inventory: InventoryStatus = InventoryStatus.OUT_OF_STOCK,
            currency: str = 'KRW',
            options: [ItemOptionData] = None
    ) -> None:
        self.id = id
        if unit is None:
            self.unit = ItemUnitData(
                unit=1,
                price=price,
                unit_type=ItemUnitType.PIECE
            )
        else:
            self.unit = unit
        self.original_price = original_price
        if self.original_price is None:
            self.original_price = price
        self.price = price
        self.delivery = delivery
        self.category = category
        self.url = url
        self.image = image
        self.name = name
        self.description = description
        self.currency = currency
        self.inventory = inventory
        self.options = options

    @property
    def total_price(self):
        return self.price
