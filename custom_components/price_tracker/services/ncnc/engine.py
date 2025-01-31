import logging
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.ncnc.const import CODE, NAME
from custom_components.price_tracker.services.ncnc.parser import NcncParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_LOGGER = logging.getLogger(__name__)
_URL = "https://qn9ovn2pnk.execute-api.ap-northeast-2.amazonaws.com/pro/items/v2/{}"
_UA = "NcncNative/605006 CFNetwork/1568.100.1 Darwin/24.0.0"
_X_API = "D3aDpWlEkz7dAp5o2Ew8zZbc4N9mnyK9JFCHgy30"


class NcncEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        id = NcncEngine.parse_id(item_url)
        self.id = id["product_id"]
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData:
        request = SafeRequest(
            proxies=self._proxies,
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
        )
        request.header(key="x-api-key", value=_X_API)
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

        logging_for_response(data, __name__, "ncnc")

        if not response.has or "error" in response.json:
            return None

        ncnc_parser = NcncParser(text=data)

        return ItemData(
            id=self.id_str(),
            name=ncnc_parser.name,
            brand=ncnc_parser.brand,
            description=ncnc_parser.description,
            price=ncnc_parser.price,
            image=ncnc_parser.image,
            url=None,
            category=ncnc_parser.category,
            inventory=ncnc_parser.inventory_status,
            delivery=ncnc_parser.delivery,
            options=[],
        )

    def id_str(self) -> str:
        return self.id

    @staticmethod
    def parse_id(item_url: str):
        return {"product_id": item_url}

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
