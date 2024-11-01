import json
import logging
import re

import aiohttp

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import ItemData, InventoryStatus
from custom_components.price_tracker.engine.engine import PriceEngine

_LOGGER = logging.getLogger(__name__)

_URL = 'https://m.apps.ssg.com/appApi/itemView.ssg'
_ITEM_LINK = 'https://emart.ssg.com/item/itemView.ssg?itemId={}&siteNo={}'


class SsgEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = SsgEngine.getId(item_url)
        self.product_id = id['product_id']
        self.site_no = id['site_no']

    async def load(self) -> ItemData:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.post(url=_URL, json={
                    "params": {
                        "dispSiteNo": str(self.site_no),
                        "itemId": str(self.product_id)
                    }
                }, headers={**REQUEST_DEFAULT_HEADERS, 'Content-Type': 'application/json'}) as response:
                    result = await response.read()

                    if response.status == 200:
                        j = json.loads(result)

                        _LOGGER.debug("SSG Response", j)

                        d = j['data']['item']

                        return ItemData(
                            id=self.product_id,
                            name=d['itemNm'],
                            price=float(d['price']['sellprc']),
                            description='',
                            url=_ITEM_LINK.format(
                                self.product_id,
                                self.site_no
                            ),
                            image=d['uitemImgList'][0]['imgUrl'] if len(d['uitemImgList']) > 0 else None,
                            category=d['ctgNm'],
                            inventory=InventoryStatus.OUT_OF_STOCK if d['itemBuyInfo'][
                                                                          'soldOut'] == 'Y' else InventoryStatus.IN_STOCK
                        )
                    else:
                        _LOGGER.error("SSG Response Error", response)

        except:
            _LOGGER.exception("SSG Error")

    def id(self) -> str:
        return "{}_{}".format(self.product_id, self.site_no)

    @staticmethod
    def getId(item_url: str):
        u = re.search(r"itemId=(?P<product_id>[\d]+)&siteNo=(?P<site_no>[\d]+)", item_url)

        if u is None:
            raise Exception("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data['product_id'] = g['product_id']
        data['site_no'] = g['site_no']

        return data
