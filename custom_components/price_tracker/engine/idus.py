import json
import logging
import re

import aiohttp

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import ItemData, DeliveryData, ItemUnitData, InventoryStatus
from custom_components.price_tracker.engine.engine import PriceEngine

_LOGGER = logging.getLogger(__name__)
_URL = 'https://api.idus.com/v3/product/info?uuid={}'
_ITEM_LINK = 'https://www.idus.com/v2/product/{}'


class IdusEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.IdusEngine = item_url
        id = IdusEngine.getId(item_url)
        self.product_id = id['product_id']

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url=_URL.format(self.product_id),
                                       headers={**REQUEST_DEFAULT_HEADERS}) as response:
                    result = await response.read()

                    if response.status == 200:
                        j = json.loads(result)
                        d = j['items']

                        _LOGGER.debug("Backpackr Idus Response", d)

                        if d['p_info']['pi_itemcount'] == -1:
                            inventory = InventoryStatus.IN_STOCK
                        elif d['p_info']['pi_itemcount'] == 0:
                            inventory = InventoryStatus.OUT_OF_STOCK
                        else:
                            inventory = InventoryStatus.ALMOST_SOLD_OUT

                        return ItemData(
                            id=d['uuid'],
                            name=d['p_info']['pi_name'],
                            price=float(d['p_info']['pi_saleprice'].replace(",", "")),
                            category=d['category_name'],
                            description=d['p_keywords'],
                            delivery=DeliveryData(
                                price=0.0
                            ),
                            url=_ITEM_LINK.format(d['uuid']),
                            image=d['p_images']['pp_mainimage']['ppi_origin']['picPath'],
                            unit=ItemUnitData(price=float(d['p_info']['pi_saleprice'].replace(",", ""))),
                            inventory=inventory
                        )
                    else:
                        _LOGGER.error("Backpackr Idus Response Error", response)

        except:
            _LOGGER.exception("Backpackr Idus Request Error")

    def id(self) -> str:
        return self.product_id

    @staticmethod
    def getId(item_url: str):
        u = re.search(r"product\/(?P<product_id>[\w\d\-]+)", item_url)

        if u is None:
            raise Exception("Bad idus item_url {}.".format(item_url))

        data = {}
        g = u.groupdict()
        data['product_id'] = g['product_id']

        return data
