import json
import logging
import re

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.kurly.const import NAME, CODE
from custom_components.price_tracker.services.kurly.parser import KurlyParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.request import http_request

_LOGGER = logging.getLogger(__name__)
_AUTH_URL = "https://www.kurly.com/nx/api/session"
_URL = "https://api.kurly.com/showroom/v2/products/{}"
_ITEM_LINK = "https://www.kurly.com/goods/{}"


class KurlyEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        self.id = KurlyEngine.parse_id(item_url)

    async def load(self) -> ItemData:
        auth_response = await http_request("get", _AUTH_URL)
        auth_data = json.loads(auth_response["data"])
        response = await http_request(
            method="get", url=_URL.format(self.id), auth=auth_data["accessToken"]
        )
        data = response["data"]
        kurly_parser = KurlyParser(text=data)
        logging_for_response(data, __name__)

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
