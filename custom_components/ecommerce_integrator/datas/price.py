from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from custom_components.price_tracker.utilities.parser import parse_float


@dataclass
class ItemPriceData:
    def __init__(
        self,
        price: float = 0.0,
        currency: str = "KRW",
        original_price: float = None,
        payback_price: float = 0.0,
    ):
        self.price = parse_float(price)
        self.currency = currency
        self.original_price = parse_float(original_price if original_price else price)
        self.discount_amount = parse_float(
            original_price - price if original_price else 0
        )
        self.discount_rate = parse_float(
            self.discount_amount / original_price * 100 if original_price else 0
        )
        self.payback_price = parse_float(payback_price)

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
    INCREMENT_PRICE = "increment_price"
    DECREMENT_PRICE = "decrement_price"
    NO_CHANGE = "no_change"

    @staticmethod
    def of(value: str):
        if value.lower() == "increment_price":
            return ItemPriceChangeStatus.INCREMENT_PRICE
        elif value.lower() == "decrement_price":
            return ItemPriceChangeStatus.DECREMENT_PRICE
        elif value.lower() == "no_change":
            return ItemPriceChangeStatus.NO_CHANGE
        else:
            raise ValueError(f"Unknown ItemPriceChangeStatus: {value}")


@dataclass
class ItemPriceSummaryData:
    def __init__(self, min_price: float = 0, max_price: float = 0):
        self.min_price = min_price
        self.max_price = max_price

    @property
    def dict(self):
        return {"min_price": self.min_price, "max_price": self.max_price}


@dataclass
class ItemPriceChangeData:
    def __init__(
        self,
        status: ItemPriceChangeStatus,
        updated_at: datetime,
        before_price: float | None = None,
        after_price: float | None = None,
    ):
        self.status = status
        self.updated_at = updated_at
        self.before_price = before_price
        self.after_price = after_price

    @property
    def dict(self):
        return {
            "status": self.status.name,
            "before_price": self.before_price,
            "after_price": self.after_price,
        }


def create_item_price_change(
    updated_at: datetime,
    period_hour: int,
    after_price: float | None = None,
    before_price: float | None = None,
) -> ItemPriceChangeData:
    if after_price is None:
        return ItemPriceChangeData(
            ItemPriceChangeStatus.NO_CHANGE, updated_at, before_price, after_price
        )

    """INC or DEC Only works in updated_at in period_hour"""
    if datetime.now().replace(tzinfo=None) - updated_at.replace(
        tzinfo=None
    ) > timedelta(hours=period_hour):
        return ItemPriceChangeData(
            ItemPriceChangeStatus.NO_CHANGE, updated_at, before_price, after_price
        )

    else:
        if before_price is None:
            return ItemPriceChangeData(
                ItemPriceChangeStatus.NO_CHANGE, updated_at, before_price, after_price
            )

        if before_price < after_price:
            return ItemPriceChangeData(
                ItemPriceChangeStatus.INCREMENT_PRICE,
                updated_at,
                before_price,
                after_price,
            )
        elif before_price > after_price:
            return ItemPriceChangeData(
                ItemPriceChangeStatus.DECREMENT_PRICE,
                updated_at,
                before_price,
                after_price,
            )
        else:
            return ItemPriceChangeData(
                ItemPriceChangeStatus.NO_CHANGE, updated_at, before_price, after_price
            )
