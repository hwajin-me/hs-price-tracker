from enum import Enum


class DeliveryPayType(Enum):
    FREE = "free"
    PAID = "paid"
    FREE_OR_PAID = "free_or_paid"


class DeliveryType(Enum):
    EXPRESS_TONIGHT = "express_night"
    EXPRESS_TODAY = "express_today"
    EXPRESS_TODAY_DAWN = "express_today_dawn"
    EXPRESS_NEXT_DAWN = "express_next_dawn"
    EXPRESS_NEXT_MORNING = "express_next_morning"
    EXPRESS_NEXT_DAY = "express_next_day"
    EXPRESS_SPECIFIC = "express_specific"
    EXPRESS = "express"
    STANDARD = "standard"
    SLOW = "slow"
    PICKUP = "pickup"
    ONLINE = "online"


class DeliveryData:
    def __init__(
        self,
        price: float = None,
        threshold_price: float = None,
        pay_type: DeliveryPayType = DeliveryPayType.FREE,
        delivery_type: DeliveryType = DeliveryType.STANDARD,
    ):
        self.price = price
        self.threshold_price = threshold_price
        self.pay_type = pay_type
        self.delivery_type = delivery_type

    def dict(self):
        return {}
