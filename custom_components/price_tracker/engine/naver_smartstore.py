import asyncio
import json
import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import ItemData, InventoryStatus, DeliveryData, DeliveryPayType, \
    ItemOptionData
from custom_components.price_tracker.engine.engine import PriceEngine

_LOGGER = logging.getLogger(__name__)

_URL = 'https://m.smartstore.naver.com/{}/products/{}'
_REQUEST_HEADER = {
    'host': 'm.smartstore.naver.com',
    'accept': 'text/html',
    'accept-encoding': 'gzip, zlib, deflate, zstd, br',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/605.1 NAVER(inapp; search; 2000; 12.8.52; 14PRO)',
}


class SmartstoreEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        id = SmartstoreEngine.getId(item_url)
        self.store = id['store']
        self.product_id = id['product_id']

    async def load(self) -> ItemData:
        response = await asyncio.to_thread(requests.get, _URL.format(self.store, self.product_id),
                                           headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADER})
        if response is not None:
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                scripts = soup.find_all("script")
                for script in scripts:
                    if "window.__PRELOADED_STATE__" in script.text:
                        data = re.search(r"window.__PRELOADED_STATE__=(?P<json>.*)", script.text)
                        json_data = json.loads(data['json'])
                        _LOGGER.debug("NAVER SmartStore Loaded at %s", datetime.now())
                        # Quantity(stock)
                        stock = InventoryStatus.IN_STOCK if json_data['product']['A'][
                                                                'stockQuantity'] > 10 else InventoryStatus.ALMOST_SOLD_OUT if \
                            json_data['product']['A']['stockQuantity'] > 0 else InventoryStatus.OUT_OF_STOCK

                        options = []
                        if 'optionCombinations' in json_data['product']['A']:
                            for option in json_data['product']['A']['optionCombinations']:
                                options.append(
                                    ItemOptionData(
                                        id = option['id'],
                                        name = option['optionName1'],
                                        price = option['price'],
                                        inventory= option['stockQuantity']
                                    )
                                )

                        return ItemData(
                            id="{}_{}".format(self.store, json_data['product']['A']['id']),
                            price=float(json_data['product']['A']['discountedSalePrice']),
                            name=json_data['product']['A']['name'],
                            description=json_data['product']['A']['detailContents']['detailContentText'],
                            category=json_data['product']['A']['category']['wholeCategoryName'],
                            image=json_data['product']['A']['representImage']['url'],
                            url=json_data['product']['A']['productUrl'],
                            inventory=stock,
                            delivery=DeliveryData(
                                price=json_data['product']['A']['productDeliveryInfo']['baseFee'],
                                type=DeliveryPayType.FREE if json_data['product']['A']['productDeliveryInfo'][
                                                                 'deliveryFeeType'] == 'FREE' else DeliveryPayType.PAID
                            ),
                            options=options if options else None
                        )
                else:
                    _LOGGER.error("NAVER Smartstore Response Parse Error %s", response)

    def id(self) -> str:
        return "{}_{}".format(self.store, self.product_id)

    @staticmethod
    def getId(item_url: str):
        u = re.search(r"smartstore\.naver\.com\/(?P<store>[a-zA-Z\d\-_]+)\/products\/(?P<product_id>[\d]+)", item_url)

        if u is None:
            raise Exception("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data['store'] = g['store']
        data['product_id'] = g['product_id']

        return data
