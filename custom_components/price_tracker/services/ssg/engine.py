import json
import logging
import re

import aiohttp

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.services.data import ItemData, InventoryStatus, ItemUnitData, ItemUnitType
from custom_components.price_tracker.services.engine import PriceEngine
from custom_components.price_tracker.utils import parseNumber

_LOGGER = logging.getLogger(__name__)

_URL = 'https://m.apps.ssg.com/appApi/itemView.ssg'
_ITEM_LINK = 'https://emart.ssg.com/item/itemView.ssg?itemId={}&siteNo={}'


class SsgEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = SsgEngine.parse_id(item_url)
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

                        if 'sellUnitPrc' in d['price']:
                            unit_data = re.search(r'^(?P<unit>[\d,]+)(?P<type>\w+) 당 : (?P<price>[\d,]+)원$',
                                                  d['price']['sellUnitPrc'])

                            if unit_data is not None:
                                unitParse = unit_data.groupdict()
                                unit = ItemUnitData(
                                    price=parseNumber(unitParse['price']),
                                    unit_type=ItemUnitType.of(unitParse['type']),
                                    unit=parseNumber(unitParse['unit'])
                                )
                            else:
                                unit = ItemUnitData(float(d['price']['sellprc']))
                        else:
                            unit = ItemUnitData(float(d['price']['sellprc']))

                        return ItemData(
                            id=self.product_id,
                            name=d['itemNm'],
                            price=parseNumber(d['price']['sellprc']),
                            description='',
                            url=_ITEM_LINK.format(
                                self.product_id,
                                self.site_no
                            ),
                            image=d['uitemImgList'][0]['imgUrl'] if len(d['uitemImgList']) > 0 else None,
                            category=d['ctgNm'],
                            inventory=InventoryStatus.OUT_OF_STOCK if d['itemBuyInfo'][
                                                                          'soldOut'] == 'Y' else InventoryStatus.IN_STOCK,
                            unit=unit
                        )
                    else:
                        _LOGGER.error("SSG Response Error", response)

        except:
            _LOGGER.exception("SSG Error")

    def id(self) -> str:
        return "{}_{}".format(self.product_id, self.site_no)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"itemId=(?P<product_id>[\d]+)&siteNo=(?P<site_no>[\d]+)", item_url)

        if u is None:
            raise Exception("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data['product_id'] = g['product_id']
        data['site_no'] = g['site_no']

        return data

    @staticmethod
    def engine_code() -> str:
        return 'ssg'

    @staticmethod
    def engine_name() -> str:
        return 'SSG'
