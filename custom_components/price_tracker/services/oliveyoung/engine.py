import re

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.oliveyoung.const import CODE, NAME
from custom_components.price_tracker.services.oliveyoung.parser import OliveyoungParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.request import http_request_async

_URL = "https://m.oliveyoung.co.kr/m/goods/getGoodsDetail.do?goodsNo={}"
_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 appVer/3.18.1 osType/10 osVer/18.0"
_THUMB = "https://image.oliveyoung.co.kr/cfimages/cf-goods/uploads/images/thumbnails/{}"


class OliveyoungEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        self.id = OliveyoungEngine.parse_id(item_url)
        self.goods_number = self.id

    async def load(self) -> ItemData:
        response = await http_request_async(
            method="get",
            url=_URL.format(self.goods_number),
            headers={"User-Agent": _UA},
        )
        logging_for_response(response, __name__)
        oliveyoung_parser = OliveyoungParser(text=response.text)

        return ItemData(
            id=self.id_str(),
            brand=oliveyoung_parser.brand,
            name=oliveyoung_parser.name,
            price=oliveyoung_parser.price,
            description=oliveyoung_parser.description,
            category=oliveyoung_parser.category,
            delivery=oliveyoung_parser.delivery,
            unit=oliveyoung_parser.unit,
            image=oliveyoung_parser.image,
            options=oliveyoung_parser.options,
            inventory=oliveyoung_parser.inventory_status,
        )

    def id_str(self) -> str:
        return self.goods_number

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"goodsNo=(?P<goods_number>[\w\d]+)", item_url)

        if u is None:
            raise InvalidItemUrlError("Bad Oliveyoung item_url " + item_url)
        g = u.groupdict()

        return g["goods_number"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
