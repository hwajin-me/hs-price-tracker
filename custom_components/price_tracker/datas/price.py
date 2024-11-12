from dataclasses import dataclass
from enum import Enum


@dataclass
class ItemPriceData:
    def __init__(
            self,
            price: float = 0.0,
            currency: str = "KRW",
            original_price: float = None,
            payback_price: float = None,
    ):
        self.price = price
        self.currency = currency
        self.original_price = original_price if original_price else price
        self.discount_amount = original_price - price if original_price else 0
        self.discount_rate = self.discount_amount / original_price * 100 if original_price else 0
        self.payback_price = payback_price

    @property
    def dict(self):
        return {
            "price": self.price,
            "currency": self.currency,
            "original_price": self.original_price,
            "discount_amount": self.discount_amount,
            "discount_rate": self.discount_rate,
            "payback_price": self.payback_price,
        }


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
    def __init__(self, status: ItemPriceChangeStatus, before_price: float | None = None,
                 after_price: float | None = None):
        self.status = status
        self.before_price = before_price
        self.after_price = after_price

    @property
    def dict(self):
        return {"status": self.status.name, "before_price": self.before_price, "after_price": self.after_price}
