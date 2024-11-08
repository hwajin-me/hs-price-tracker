from enum import Enum


class InventoryStatus(Enum):
    IN_STOCK = 'in_stock'
    ALMOST_SOLD_OUT = 'almost_sold_out'
    OUT_OF_STOCK = 'out_of_stock'

    @staticmethod
    def of(is_sold_out: bool, stock: int = None):
        if is_sold_out:
            return InventoryStatus.OUT_OF_STOCK
        elif not is_sold_out and stock is not None and stock < 10:
            return InventoryStatus.ALMOST_SOLD_OUT
        else:
            return InventoryStatus.IN_STOCK
