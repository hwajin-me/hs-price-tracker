import re
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
    NotFoundError,
)
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.rankingdak.const import (
    CODE,
    NAME,
)
from custom_components.price_tracker.services.rankingdak.parser import RankingdakParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_URL = "https://m.rankingdak.com/product/view?productCd={}"


class RankingdakEngine(PriceEngine):
    def __init__(
        self,
        item_url: str,
        device: None = None,
        proxies: Optional[list] = None,
        selenium: Optional[str] = None,
        selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = RankingdakEngine.parse_id(item_url)
        self.product_id = self.id
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
        request.accept_text_html()
        request.user_agent(mobile_random=True)
        response = await request.request(
            method=SafeRequestMethod.GET, url=_URL.format(self.product_id)
        )

        if response.is_not_found or not response.has:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
            )

        logging_for_response(response, __name__, "rankingdak")

        try:
            parser = RankingdakParser(html=response.data)

            return ItemData(
                id=self.id_str(),
                brand=parser.brand,
                name=parser.name,
                price=parser.price,
                description=parser.description,
                category=parser.category,
                delivery=parser.delivery,
                unit=parser.unit,
                image=parser.image,
                url="https://www.rankingdak.com/product/view?productCd={}".format(
                    self.id
                ),
                options=parser.options,
                inventory=parser.inventory_status,
            )
        except NotFoundError as e:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
            )
        except Exception as e:
            raise e

    def id_str(self) -> str:
        return self.product_id

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"productCd=(?P<product_id>\w+)", item_url)

        if u is None:
            raise InvalidItemUrlError("Bad Rankingdak item_url " + item_url)
        g = u.groupdict()

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
