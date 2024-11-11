from dataclasses import dataclass
from enum import Enum


@dataclass
class ItemPriceData:
    def __init__(
            self,
            price: float = 0.0,
            currency: str = "KRW",
            original_price: float = None,
            discount_price: float = None,
            discount_rate: float = None,
            payback_price: float = None,
    ):
        self.price = price
        self.currency = currency
        self.original_price = original_price if original_price else price
        self.discount_price = discount_price
        self.discount_rate = discount_rate
        self.payback_price = payback_price


class ItemPriceChangeStatus(Enum):
    INCREMENT_PRICE = ("increment_price",)
    DECREMENT_PRICE = ("decrement_price",)
    NO_CHANGE = "no_change"


@dataclass
class ItemPriceSummaryData:
    def __init__(self, min_price: float = None, max_price: float = None):
        self.min_price = min_price
        self.max_price = max_price

    @property
    def dict(self):
        return {"min_price": self.min_price, "max_price": self.max_price}


@dataclass
class ItemPriceChangeData:
    def __init__(self, status: ItemPriceChangeStatus, before_price: float | None = None, after_price: float | None = None):
        self.status = status
        self.before_price = before_price
        self.after_price = after_price

    @property
    def dict(self):
        return {"status": self.status.name, "before_price": self.before_price, "after_price": self.after_price}
