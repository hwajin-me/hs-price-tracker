import dataclasses

from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import DeliveryData
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
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
            price: ItemPriceData,
            name: str,
            brand: str = None,
            description: str = None,
            category: ItemCategoryData = None,
            delivery: DeliveryData = None,
            url: str = None,
            image: str = None,
            unit: ItemUnitData = None,
            inventory: InventoryStatus = InventoryStatus.OUT_OF_STOCK,
            options: [ItemOptionData] = None,
    ) -> None:
        self.id = id
        if unit is None:
            self.unit = ItemUnitData(unit=1, price=price.price, unit_type=ItemUnitType.PIECE)
        else:
            self.unit = unit
        self.price = price
        self.brand = brand
        self.delivery = delivery
        self.category = category
        self.url = url
        self.image = image
        self.name = name
        self.description = description
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
            'display_category': self.category.split if self.category is not None else None,
            'price': self.price.dict,
            'delivery': self.delivery.dict if self.delivery is not None else None,
            'url': self.url,
            'image': self.image,
            'inventory_status': self.inventory.name,
            'unit': self.unit.dict,
            'options': [option.dict for option in self.options] if self.options is not None else None,
        }
