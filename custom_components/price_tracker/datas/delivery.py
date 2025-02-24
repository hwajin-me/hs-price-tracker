import dataclasses
import datetime
from enum import Enum


class DeliveryPayType(Enum):
    FREE = "free"
    PAID = "paid"
    FREE_OR_PAID = "free_or_paid"
    UNKNOWN = "unknown"


class DeliveryType(Enum):
    EXPRESS_TONIGHT = "express_night"
    EXPRESS_TODAY = "express_today"
    EXPRESS_TODAY_DAWN = "express_today_dawn"
    EXPRESS_NEXT_DAWN = "express_next_dawn"
    EXPRESS_NEXT_MORNING = "express_next_morning"
    EXPRESS_NEXT_DAY = "express_next_day"
    EXPRESS_SPECIFIC = "express_specific"
    EXPRESS_SPECIFIC_DAWN = "express_specific_dawn"
    EXPRESS = "express"
    STANDARD = "standard"
    SLOW = "slow"
    PICKUP = "pickup"
    NO_DELIVERY = "no_delivery"


class DeliveryStatus(Enum):
    CREATED = "created"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_SUCCESS = "payment_success"
    PARTIAL_CANCELLED = "partial_cancelled"
    CANCELLED = "cancelled"
    STOCK_NOT_AVAILABLE = "stock_not_available"
    ITEM_SENT = "item_sent"
    COURIER_PICKUP = "courier_pickup"
    IMPORTED = "imported"
    PACKAGING_REQUESTED = "packaging_requested"
    PACKAGING_COMPLETED = "packaging_completed"
    PACKAGING_FAILED = "packaging_failed"
    EXPORT_REQUESTED = "export_requested"
    EXPORTED = "exported"
    EXPORT_FAILED = "export_failed"
    SHIPPED = "shipped"
    CUSTOMS_CLEARANCE_REQUESTED = "customs_clearance_requested"
    CUSTOMS_CLEARANCE_COMPLETED = "customs_clearance_completed"
    CUSTOMS_CLEARANCE_FAILED = "customs_clearance_failed"
    LOCAL_DELIVERY_COMPANY_PICKUP = "local_delivery_company_pickup"
    LOCAL_DELIVERY_COMPANY_DELIVERED = "local_delivery_company_delivered"


@dataclasses.dataclass
class DeliveryData:
    def __init__(
        self,
        price: float = None,
        threshold_price: float = None,
        minimum_price: float = None,
        pay_type: DeliveryPayType = DeliveryPayType.UNKNOWN,
        delivery_type: DeliveryType = DeliveryType.NO_DELIVERY,
        arrive_date: datetime.date = None,
    ):
        self.price = price
        self.threshold_price = threshold_price
        self.minimum_price = minimum_price
        self.pay_type = pay_type
        self.delivery_type = delivery_type
        self.arrive_date = arrive_date

