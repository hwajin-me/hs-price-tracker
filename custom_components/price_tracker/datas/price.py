from enum import Enum


class ItemPriceData:
    def __init__(self, price: float = 0.0, currency: str = 'KRW', original_price: float = None,
                 discount_price: float = None, discount_rate: float = None, payback_price: float = None):
        self.price = price
        self.currency = currency
        self.original_price = original_price if original_price else price
        self.discount_price = discount_price
        self.discount_rate = discount_rate
        self.payback_price = payback_price


class ItemPriceChangeStatus(Enum):
    INCREMENT_PRICE = 'increment_price',
    DECREMENT_PRICE = 'decrement_price',
    NO_CHANGE = 'no_change'


class ItemPriceSummaryData:
    def __init__(self, min_price: float = None, max_price: float = None):
        self.min_price = min_price
        self.max_price = max_price

    @property
    def dict(self):
        return {
            'min_price': self.min_price,
            'max_price': self.max_price
        }
