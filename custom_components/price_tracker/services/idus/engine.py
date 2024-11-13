import re

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.idus.parser import IdusParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.request import http_request

_URL = "https://api.idus.com/v3/product/info?uuid={}"
_ITEM_LINK = "https://www.idus.com/v2/product/{}"


class IdusEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        self.id = IdusEngine.parse_id(item_url)
        self.product_id = self.id

    async def load(self) -> ItemData:
        response = await http_request(method="get", url=_URL.format(self.product_id))
        data = response["data"]
        idus_parser = IdusParser(text=data)
        logging_for_response(data, __name__)

        return ItemData(
            id=self.id_str(),
            name=idus_parser.name,
            description=idus_parser.description,
            brand=idus_parser.brand,
            price=idus_parser.price,
            category=idus_parser.category,
            delivery=idus_parser.delivery,
            inventory=idus_parser.inventory_status,
            url=idus_parser.url,
            unit=idus_parser.unit,
            image=idus_parser.image,
            options=idus_parser.options,
        )

    def id_str(self) -> str:
        return self.product_id

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"product/(?P<product_id>[\w\d\-]+)", item_url)

        if u is None:
            raise InvalidItemUrlError(
                'Bad backpackr(idus) item_url "{}".'.format(item_url)
            )

        g = u.groupdict()

        return g["product_id"]

    @staticmethod
    def engine_code() -> str:
        return "idus"

    @staticmethod
    def engine_name() -> str:
        return "Idus"
