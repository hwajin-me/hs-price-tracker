import dataclasses

from custom_components.price_tracker.datas.delivery import DeliveryData
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType


@dataclasses.dataclass
class ItemOptionData:
    def __init__(self, id: any, name: str, price: float, inventory: int = None):
        self.id = id
        self.name = name
        self.price = price
        self.inventory = InventoryStatus.of(is_sold_out=False, stock=inventory)

    @property
    def dict(self):
        return {
            'option_id': self.id,
            'name': self.name,
            'price': self.price,
            'inventory_status': self.inventory.name,
        }

@dataclasses.dataclass
class ItemData:
    def __init__(
            self,
            id: any,
            price: float,
            name: str,
            brand: str = None,
            original_price: float = None,
            description: str = None,
            category: str = None,
            delivery: DeliveryData = None,
            url: str = None,
            image: str = None,
            unit: ItemUnitData = None,
            inventory: InventoryStatus = InventoryStatus.OUT_OF_STOCK,
            currency: str = "KRW",
            options: [ItemOptionData] = None,
    ) -> None:
        self.id = id
        if unit is None:
            self.unit = ItemUnitData(unit=1, price=price, unit_type=ItemUnitType.PIECE)
        else:
            self.unit = unit
        self.original_price = original_price
        if self.original_price is None:
            self.original_price = price
        self.price = price
        self.brand = brand
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

    @property
    def dict(self):
        return {
            'product_id': self.id,
            'brand': self.brand,
            'name': self.name,
            'description': self.description,
            'display_category': self.category,
            'price': self.price,
            'original_price': self.original_price,
            'delivery': self.delivery.dict if self.delivery is not None else None,
            'url': self.url,
            'image': self.image,
            'inventory_status': self.inventory.name,
            'currency': self.currency,
            'unit': self.unit.dict,
            'options': [option.dict for option in self.options] if self.options is not None else None,
        }
