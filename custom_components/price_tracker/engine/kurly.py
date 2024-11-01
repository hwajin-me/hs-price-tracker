import json
import logging
import re

import aiohttp

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import ItemData, DeliveryData, DeliveryPayType, InventoryStatus
from custom_components.price_tracker.engine.engine import PriceEngine

_LOGGER = logging.getLogger(__name__)
_AUTH_URL = 'https://www.kurly.com/nx/api/session'
_URL = 'https://api.kurly.com/showroom/v2/products/{}'
_ITEM_LINK = 'https://www.kurly.com/goods/{}'


class KurlyEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = KurlyEngine.getId(item_url)
        self.product_id = id['product_id']

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url=_AUTH_URL, headers={**REQUEST_DEFAULT_HEADERS}) as auth:
                    auth_result = await auth.read()

                    if auth.status == 200:
                        auth_data = json.loads(auth_result)
                        async with session.get(url=_URL.format(self.product_id), headers={**REQUEST_DEFAULT_HEADERS,
                            'Authorization': 'Bearer {}'.format(
                                auth_data[
                                    'accessToken'])}) as response:
                            result = await response.read()

                            if response.status == 200:
                                j = json.loads(result)
                                d = j['data']

                                _LOGGER.debug("Kurly Response", d)

                                return ItemData(
                                    id=d['no'],
                                    name=d['name'],
                                    price=float(d['retail_price']),
                                    image=d['main_image_url'],
                                    description=d['short_description'],
                                    category=d['category_ids'].join('>'),
                                    delivery=DeliveryData(
                                        price=0.0,
                                        type=DeliveryPayType.FREE if d['is_direct_order'] else DeliveryPayType.PAID
                                    ),
                                    url=_ITEM_LINK.format(d['no']),
                                    inventory=InventoryStatus.IN_STOCK if not d[
                                        'is_sold_out'] else InventoryStatus.OUT_OF_STOCK
                                )
                            else:
                                _LOGGER.error("Kurly Fetch Request Error", response)
                    else:
                        _LOGGER.error("Kurly Authentication Request Error")

        except:
            _LOGGER.exception("Kurly Request Error")

    def id(self) -> str:
        return self.product_id

    @staticmethod
    def getId(item_url: str):
        u = re.search(r"(?:goods|products)\/(?P<product_id>[\d]+)", item_url)

        if u is None:
            raise Exception("Bad Kurly item_url {}.".format(item_url))

        data = {}
        g = u.groupdict()
        data['product_id'] = g['product_id']

        return data
