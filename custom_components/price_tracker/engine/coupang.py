import json
import logging
import re
from datetime import datetime

import aiohttp
import requests
import asyncio
from bs4 import BeautifulSoup

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import DeliveryPayType, ItemData, ItemUnitType, ItemUnitData, InventoryStatus, \
    DeliveryData
from custom_components.price_tracker.engine.engine import PriceEngine
from custom_components.price_tracker.utils import findItem

_LOGGER = logging.getLogger(__name__)

_URL = 'https://m.coupang.com/vm/products/{}?itemId={}&vendorItemId={}'
_ITEM_LINK = 'https://www.coupang.com/vp/products/{}?itemId={}&vendorItemId={}'
_REQUEST_HEADERS = {
    'Sec-Ch-Ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'Sec-Ch-Ua-Platform': '"Android"',
    'Sec-Fetch-Dest': 'document',
    'Priority': 'u=0, i',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    'Cookie': 'PCID=0'
}

class CoupangEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        data = CoupangEngine.getId(item_url)

        self.product_id = data['product_id']
        self.item_id = data['item_id']
        self.vendor_item_id = data['vendor_item_id']

    async def load(self) -> ItemData:
        try:
            response = await asyncio.to_thread(requests.get, _URL.format(self.product_id, self.item_id, self.vendor_item_id), headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS})
            if response is not None:
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    if soup is not None:
                        data = soup.find("script", {"id": "__NEXT_DATA__"}).get_text()
                        j = json.loads(data)
                        _LOGGER.debug("Coupang Fetched at {}".format(datetime.now()))

                        pageAtf = findItem(j['props']['pageProps']['pageList'], 'page', 'PAGE_ATF')

                        if pageAtf is None:
                            raise Exception("Coupang Parse Error (No ATF) - {}".format(data))
                        pageAtf = pageAtf['widgetList']

                        name = findItem(pageAtf, 'viewType', 'MWEB_PRODUCT_DETAIL_PRODUCT_INFO')['data']['title']
                        price = findItem(pageAtf, 'viewType', 'MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO')['data']['finalPrice']['price']
                        priceInfo = findItem(pageAtf, 'viewType', 'MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO')['data']
                        deliveryPrice = priceInfo['deliveryMessages'] if 'deliveryMessage' in priceInfo else None
                        deliveryType = DeliveryPayType.PAID
                        if deliveryPrice is not None:
                            deliveryPrice = float(deliveryPrice.replace("배송비", "").replace("원", "").replace(",", "").replace(" ", ""))
                        else:
                            deliveryPrice = 0.0
                            deliveryType = DeliveryPayType.FREE

                        description = ''
                        image = findItem(pageAtf, 'viewType', 'MWEB_PRODUCT_DETAIL_ITEM_THUMBNAILS')['data']['medias'][0]['detail']
                        category = ">".join(str(t['name']) for t in findItem(pageAtf, 'viewType', 'MWEB_PRODUCT_DETAIL_SDP_BREADCURMB_DETAIL')['data']['breadcrumb'] if t['linkcode'] != '0')

                        if 'unitPriceDescription' in priceInfo['finalPrice']:
                            u = re.match(r"^\((?P<per>[\d,]+)(?P<unit_type>g|개|ml|kg|l)당 (?P<price>[\d,]+)원\)$",
                                         priceInfo['finalPrice']['unitPriceDescription'])
                            g = u.groupdict()
                            unit_price = ItemUnitData(
                                unit_type=ItemUnitType.of(g['unit_type']),
                                unit=float(g['per'].replace(',', '')),
                                price=float(g['price'].replace(',', ''))
                            )
                        else:
                            unit_price = ItemUnitData(price=price)

                        inventory = findItem(pageAtf, 'viewType', 'MWEB_PRODUCT_DETAIL_ATF_QUANTITY')['data'] if findItem(pageAtf, 'viewType', 'MWEB_PRODUCT_DETAIL_ATF_QUANTITY') is not None else None
                        soldOut = j['props']['pageProps']['properties']['itemDetail']['soldOut']

                        if (inventory is None or 'limitMessage' not in inventory) and soldOut == False:
                            stock = InventoryStatus.IN_STOCK
                        elif soldOut == False and inventory is None:
                            stock = InventoryStatus.IN_STOCK
                        elif soldOut == False and 'limitMessage' in inventory:
                            stock = InventoryStatus.ALMOST_SOLD_OUT
                        else:
                            stock = InventoryStatus.OUT_OF_STOCK

                        return ItemData(
                            id="{}_{}_{}".format(self.product_id, self.item_id, self.vendor_item_id),
                            price=price,
                            name=name,
                            description=description,
                            url=_ITEM_LINK.format(self.product_id, self.item_id, self.vendor_item_id),
                            image=image,
                            delivery=DeliveryData(
                                price=deliveryPrice,
                                type=deliveryType
                            ),
                            unit=unit_price,
                            category=category,
                            inventory=stock,
                        )
                    else:
                        raise Exception("Coupang unknown request exception {}".format(response))
        except:
            _LOGGER.exception("Coupang Parse Error")

    def id(self) -> str:
        return "{}_{}".format(self.product_id, self.vendor_item_id)

    @staticmethod
    def getId(item_url: str):
        u = re.search(r"products\/(?P<product_id>[\d]+)\?itemId=(?P<item_id>[\d]+).*?(?:|vendorItemId=(?P<vendor_item_id>[\d]+).*)$", item_url)

        if u is None:
            raise Exception("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data['product_id'] = g['product_id']
        data['item_id'] = g['item_id']
        data['vendor_item_id'] = ''
        if 'vendor_item_id' in g:
            data['vendor_item_id'] = g['vendor_item_id']
        return data
