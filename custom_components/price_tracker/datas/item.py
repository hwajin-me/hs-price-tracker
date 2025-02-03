import dataclasses
from enum import Enum

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
            "option_id": self.id,
            "name": self.name,
            "price": self.price,
            "inventory_status": self.inventory.name,
        }


class ItemStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"


@dataclasses.dataclass
class ItemData:
    def __init__(
        self,
        id: any,
        name: str = "UNKNOWN",
        price: ItemPriceData = ItemPriceData(),
        brand: str = None,
        description: str = None,
        category: ItemCategoryData = None,
        delivery: DeliveryData = DeliveryData(),
        url: str = None,
        image: str = None,
        unit: ItemUnitData = None,
        inventory: InventoryStatus = InventoryStatus.OUT_OF_STOCK,
        options: [ItemOptionData] = None,
        status: ItemStatus = ItemStatus.ACTIVE,
        http_status: int = 200,
    ) -> None:
        self.id = id
        if unit is None:
            self.unit = ItemUnitData(
                unit=1, price=price.price, unit_type=ItemUnitType.PIECE
            )
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
        self.status = status
        self.http_status = http_status

    @property
    def total_price(self):
        return self.price

    @property
    def dict(self):
        data = {
            "product_id": self.id,
            "brand": self.brand,
            "name": self.name,
            "description": self.description,
            "display_category": self.category.split
            if self.category is not None
            else None,
            "display_category_last": self.category.last
            if self.category is not None
            else None,
            "original_price": self.price.original_price,
            "price": self.price.price,
            "discount_rate": self.price.discount_rate,
            "discount_amount": self.price.discount_amount,
            "payback_price": self.price.payback_price,
            "currency": self.price.currency,
            "delivery_type": self.delivery.delivery_type.name,
            "delivery_pay_type": self.delivery.pay_type.name,
            "delivery_price": self.delivery.price,
            "delivery_free_threshold_price": self.delivery.threshold_price,
            "delivery_minimum_price": self.delivery.minimum_price,
            "delivery_arrive_date": self.delivery.arrive_date,
            "url": self.url,
            "image": self.image,
            "inventory_status": self.inventory.name,
            "inventory_status_rank": self.inventory.rank,
            "unit_value": self.unit.unit,
            "unit_type": self.unit.unit_type.name,
            "unit_price": self.unit.price,
            "sort_price": "{}:{}".format(
                str(self.price.price).ljust(12, "0"), self.inventory.lower_rank
            ),
            "product_options": [option.dict for option in self.options]
            if self.options is not None
            else [],
            "status": self.status.name
            if self.status is not None
            else ItemStatus.ACTIVE.name,
            "http_status": self.http_status,
        }

        # For fast-access options
        if self.options is not None:
            for idx, option in enumerate(self.options):
                data[f"product_option_{idx}_id"] = option.id
                data[f"product_option_{idx}_name"] = option.name
                data[f"product_option_{idx}_price"] = option.price
                data[f"product_option_{idx}_quantity"] = option.inventory

        return data
