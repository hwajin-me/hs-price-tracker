import logging
import re
from urllib.parse import unquote

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
    ApiAuthError,
)
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.gsthefresh.const import CODE, NAME
from custom_components.price_tracker.services.gsthefresh.device import GsTheFreshDevice
from custom_components.price_tracker.services.gsthefresh.parser import GsthefreshParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.request import (
    http_request,
)

_UA = "Dart/3.5 (dart:io)"
_REQUEST_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "appinfo_device_id": "a00000a0fa004cf127333873c60e5b12",
    "device_id": "a00000a0fa004cf127333873c60e5b12",
}
_LOGIN_URL = "https://b2c-bff.woodongs.com/api/bff/v2/auth/accountLogin"
_REAUTH_URL = "https://b2c-apigw.woodongs.com/auth/v1/token/reissue"
_PRODUCT_URL = "https://b2c-apigw.woodongs.com/supermarket/v1/wdelivery/item/{}?pickupItemYn=Y&storeCode={}"
_ITEM_LINK = "https://woodongs.com/link?view=gsTheFreshDeliveryDetail&orderType=pickup&itemCode={}"

_LOGGER = logging.getLogger(__name__)


class GsTheFreshEngine(PriceEngine):
    def __init__(self, item_url: str, device: GsTheFreshDevice):
        self.item_url = item_url
        self.id = GsTheFreshEngine.parse_id(item_url)
        self.device: GsTheFreshDevice = device
        self._last_failed = False

    async def load(self) -> ItemData:
        try:
            http_result = await http_request(
                "get",
                _PRODUCT_URL.format(self.id, self.device.store),
                headers={**_REQUEST_HEADERS, **self.device.headers},
                auth=self.device.access_token,
                timeout=5,
            )
        except ApiAuthError as e:
            self.device.invalid()
            if self._last_failed is False:
                self._last_failed = True
            else:
                raise e
            http_result = await http_request(
                "get",
                _PRODUCT_URL.format(self.id, self.device.store),
                headers={**_REQUEST_HEADERS, **self.device.headers},
                auth=self.device.access_token,
                timeout=5,
            )

        result = http_result["data"]
        gs_parser = GsthefreshParser(text=result)
        logging_for_response(result, __name__)

        return ItemData(
            id=self.id_str(),
            name=gs_parser.name,
            description=gs_parser.description,
            brand=gs_parser.brand,
            image=gs_parser.image,
            url=_ITEM_LINK.format(self.id),
            delivery=gs_parser.delivery,
            unit=gs_parser.unit,
            options=[],
            category=gs_parser.category,
            price=gs_parser.price,
        )

    def id_str(self) -> str:
        return "{}_{}".format(self.device.store, self.id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"itemCode=(?P<product_id>\d+)", unquote(item_url))
        g = u.groupdict()

        if g is None:
            raise InvalidItemUrlError("GS THE FRESH Item ID Parse(Regex) Error")

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME

    def url(self) -> str:
        return self.item_url
