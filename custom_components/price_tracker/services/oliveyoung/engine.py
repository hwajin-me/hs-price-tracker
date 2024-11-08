import asyncio
import json
import logging
import re

import requests
from bs4 import BeautifulSoup

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.services.data import ItemData, InventoryStatus
from custom_components.price_tracker.services.engine import PriceEngine

_LOGGER = logging.getLogger(__name__)

_URL = 'https://m.oliveyoung.co.kr/m/goods/getGoodsDetail.do?goodsNo={}'
_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 appVer/3.18.1 osType/10 osVer/18.0'
_THUMB = 'https://image.oliveyoung.co.kr/cfimages/cf-goods/uploads/images/thumbnails/{}'


class OliveyoungEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = OliveyoungEngine.parse_id(item_url)
        self.goods_number = id['goods_number']

    async def load(self) -> ItemData:
        try:
            response = await asyncio.to_thread(requests.get, _URL.format(self.goods_number),
                                               headers={**REQUEST_DEFAULT_HEADERS, 'User-Agent': _UA})
            if response is not None:
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    data = soup.find("textarea", {"id": "goodsData"}).get_text()
                    if data is not None:
                        json_data = json.loads(data)

                        _LOGGER.debug("Oliveyoung Response", json_data)

                        return ItemData(
                            id=self.goods_number,
                            price=float(json_data['finalPrice']),
                            name=json_data['goodsBaseInfo']['goodsName'],
                            category=json_data['displayCategoryInfo']['displayCategoryFullPath'],
                            description=json_data['brandName'],
                            image=_THUMB.format(json_data['images'][0]) if len(json_data['images']) else None,
                            inventory=InventoryStatus.OUT_OF_STOCK if json_data['optionInfo'][
                                'allSoldoutFlag'] else InventoryStatus.IN_STOCK
                        )
                    else:
                        _LOGGER.error("Oliveyoung Response Parse Error", response.request_info, response)
        except:
            _LOGGER.exception("Oliveyoung Request Parse Error")

    def id(self) -> str:
        return self.goods_number

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"goodsNo=(?P<goods_number>[\w\d]+)", item_url)

        if u is None:
            raise Exception("Bad Oliveyoung item_url " + item_url)
        data = {}
        g = u.groupdict()
        data['goods_number'] = g['goods_number']

        return data

    @staticmethod
    def engine_code() -> str:
        return 'oliveyoung'

    @staticmethod
    def engine_name() -> str:
        return 'Oliveyoung'
