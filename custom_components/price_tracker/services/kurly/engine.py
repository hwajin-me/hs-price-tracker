import logging
import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.kurly.const import NAME, CODE
from custom_components.price_tracker.services.kurly.parser import KurlyParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_LOGGER = logging.getLogger(__name__)
_AUTH_URL = "https://api.kurly.com/v3/auth/guest"
_URL = "https://api.kurly.com/showroom/v2/products/{}"
_ITEM_LINK = "https://www.kurly.com/goods/{}"


class KurlyEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = KurlyEngine.parse_id(item_url)
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData | None:
        request = SafeRequest(
            proxies=self._proxies,
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
        )
        auth_response = await request.request(
            method=SafeRequestMethod.POST, url=_AUTH_URL
        )
        auth_data = auth_response.json
        request.auth(auth_data["data"]["access_token"])
        response = await request.request(
            method=SafeRequestMethod.GET, url=_URL.format(self.id)
        )

        if response.is_not_found:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
            )

        data = response.data

        logging_for_response(data, __name__, "kurly")

        kurly_parser = KurlyParser(text=data)

        return ItemData(
            id=self.id_str(),
            name=kurly_parser.name,
            brand=kurly_parser.brand,
            description=kurly_parser.description,
            image=kurly_parser.image,
            category=kurly_parser.category,
            delivery=kurly_parser.delivery,
            unit=kurly_parser.unit,
            price=kurly_parser.price,
            inventory=kurly_parser.inventory,
            options=kurly_parser.options,
        )

    def id_str(self) -> str:
        return self.id

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"(?:goods|products)/(?P<product_id>[\d]+)", item_url)

        if u is None:
            raise InvalidItemUrlError("Bad Kurly item_url {}.".format(item_url))

        g = u.groupdict()

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
