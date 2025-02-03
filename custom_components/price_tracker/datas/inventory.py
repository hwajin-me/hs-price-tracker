from enum import Enum


class InventoryStatus(Enum):
    IN_STOCK = "in_stock", 10, 0
    ALMOST_SOLD_OUT = "almost_sold_out", 1, 1
    OUT_OF_STOCK = "out_of_stock", 0, 2

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        obj._value_ = values[0]
        obj._rank = values[1]
        obj._lower_rank = values[2]
        for other_value in values[1:]:
            cls._value2member_map_[other_value] = obj
        obj._all_values = values
        return obj

    def __repr__(self):
        return "<%s.%s: %s>" % (
            self.__class__.__name__,
            self._name_,
            ", ".join([repr(v) for v in self._all_values]),
        )

    @property
    def rank(self):
        return self._rank

    @property
    def lower_rank(self):
        return self._lower_rank

    @staticmethod
    def of(is_sold_out: bool = False, stock: int = None):
        if is_sold_out:
            return InventoryStatus.OUT_OF_STOCK
        elif not is_sold_out and stock is not None and stock < 10:
            return InventoryStatus.ALMOST_SOLD_OUT
        else:
            return InventoryStatus.IN_STOCK
