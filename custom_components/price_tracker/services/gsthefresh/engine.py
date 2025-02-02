import logging
import re
from typing import Optional
from urllib.parse import unquote

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.gsthefresh.const import CODE, NAME
from custom_components.price_tracker.services.gsthefresh.device import GsTheFreshDevice
from custom_components.price_tracker.services.gsthefresh.parser import GsthefreshParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
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
    def __init__(
        self,
        item_url: str,
        device: GsTheFreshDevice,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = GsTheFreshEngine.parse_id(item_url)
        self.device: GsTheFreshDevice = device
        self._last_failed = False
        self._proxies = proxies
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData:
        request = SafeRequest(
            selenium=self._selenium, selenium_proxy=self._selenium_proxy
        )
        request.headers({**_REQUEST_HEADERS, **self.device.headers})
        request.auth(self.device.access_token)
        http_result = await request.request(
            method=SafeRequestMethod.GET,
            url=_PRODUCT_URL.format(self.id, self.device.store),
        )

        result = http_result.data

        if http_result.is_not_found:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
            )

        logging_for_response(result, __name__, "gsthefresh")
        gs_parser = GsthefreshParser(text=result)

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
            inventory=gs_parser.inventory_status,
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
