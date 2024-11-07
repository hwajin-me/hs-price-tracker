import json
import logging
from datetime import datetime

import aiohttp

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import ItemData, InventoryStatus
from custom_components.price_tracker.engine.engine import PriceEngine

_LOGGER = logging.getLogger(__name__)
_URL = 'https://qn9ovn2pnk.execute-api.ap-northeast-2.amazonaws.com/pro/items/v2/{}'
_UA = 'NcncNative/605006 CFNetwork/1568.100.1 Darwin/24.0.0'
_X_API = 'D3aDpWlEkz7dAp5o2Ew8zZbc4N9mnyK9JFCHgy30'


class NcncEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = NcncEngine.getId(item_url)
        self.product_id = id['product_id']

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url=_URL.format(self.product_id),
                                       headers={**REQUEST_DEFAULT_HEADERS, 'User-Agent': _UA,
                                                'x-api-key': _X_API}) as response:
                    result = await response.read()

                    if response.status == 200:
                        j = json.loads(result)
                        _LOGGER.debug("NCNC Fetched at {} - {}", datetime.now(), self.product_id)

                        d = j['item']

                        # TODO : Find real item

                        return ItemData(
                            id=d['id'],
                            name=d['name'],
                            price=float(d['conItems'][0]['minSellingPrice']) if len(d['conItems']) and d['conItems'][
                                0] else d[
                                'originalPrice'],
                            description=d['conItems'][0]['info'] if len(d['conItems']) else '',
                            image=d['imageUrl'],
                            category="{}>{}".format(d['conCategory2']['conCategory1']['name'],
                                                    d['conCategory2']['name']),
                            inventory=InventoryStatus.OUT_OF_STOCK if d['isSoldOut'] else InventoryStatus.IN_STOCK,
                            # NO-DELIVERY ITEM(digital)
                        )
                    else:
                        _LOGGER.error("NCNC Response Error", response)

        except:
            _LOGGER.exception("NCNC Request Error")

    def id(self) -> str:
        return self.product_id

    @staticmethod
    def getId(item_url: str):
        return {
            "product_id": item_url
        }
