from custom_components.price_tracker.datas.delivery import DeliveryData
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType


class ItemOptionData:
    def __init__(self, id: any, name: str, price: float, inventory: int = None):
        self.id = id
        self.name = name
        self.price = price
        if inventory is not None:
            if inventory > 10:
                self.inventory = InventoryStatus.IN_STOCK
            elif inventory > 0:
                self.inventory = InventoryStatus.ALMOST_SOLD_OUT
            else:
                self.inventory = InventoryStatus.OUT_OF_STOCK


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

    @property
    def dict(self):
        return {

        }
