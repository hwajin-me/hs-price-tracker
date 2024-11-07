import asyncio
import json
import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import DeliveryPayType, ItemData, ItemUnitType, ItemUnitData, \
    InventoryStatus, \
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
            response = await asyncio.to_thread(requests.get,
                                               _URL.format(self.product_id, self.item_id, self.vendor_item_id),
                                               headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS})
            if response is not None:
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    if soup is not None:
                        data = soup.find("script", {"id": "__NEXT_DATA__"}).get_text()
                        j = json.loads(data)
                        _LOGGER.debug("Coupang Fetched at {}".format(datetime.now()))
                        page_atf = findItem(j['props']['pageProps']['pageList'], 'page', 'PAGE_ATF')
                        if page_atf is None:
                            raise Exception("Coupang Parse Error (No ATF) - {}".format(data))
                        page_atf = page_atf['widgetList']

                        name = findItem(page_atf, 'viewType', 'MWEB_PRODUCT_DETAIL_PRODUCT_INFO')['data']['title']
                        price = \
                        findItem(page_atf, 'viewType', 'MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO')['data']['finalPrice'][
                            'price']
                        price_info = findItem(page_atf, 'viewType', 'MWEB_PRODUCT_DETAIL_ATF_PRICE_INFO')['data']
                        delivery_price = price_info['deliveryMessages'] if 'deliveryMessage' in price_info else None
                        delivery_type = DeliveryPayType.PAID
                        if delivery_price is not None:
                            delivery_price = float(
                                delivery_price.replace("배송비", "").replace("원", "").replace(",", "").replace(" ", ""))
                        else:
                            delivery_price = 0.0
                            delivery_type = DeliveryPayType.FREE

                        description = ''
                        image = \
                        findItem(page_atf, 'viewType', 'MWEB_PRODUCT_DETAIL_ITEM_THUMBNAILS')['data']['medias'][0][
                            'detail']
                        category = ">".join(str(t['name']) for t in
                                            findItem(page_atf, 'viewType', 'MWEB_PRODUCT_DETAIL_SDP_BREADCURMB_DETAIL')[
                                                'data']['breadcrumb'] if t['linkcode'] != '0')

                        if 'unitPriceDescription' in price_info['finalPrice']:
                            u = re.match(r"^\((?P<per>[\d,]+)(?P<unit_type>g|개|ml|kg|l)당 (?P<price>[\d,]+)원\)$",
                                         price_info['finalPrice']['unitPriceDescription'])
                            g = u.groupdict()
                            unit_price = ItemUnitData(
                                unit_type=ItemUnitType.of(g['unit_type']),
                                unit=float(g['per'].replace(',', '')),
                                price=float(g['price'].replace(',', ''))
                            )
                        else:
                            unit_price = ItemUnitData(price=price)

                        inventory = findItem(page_atf, 'viewType', 'MWEB_PRODUCT_DETAIL_ATF_QUANTITY')[
                            'data'] if findItem(page_atf, 'viewType',
                                                'MWEB_PRODUCT_DETAIL_ATF_QUANTITY') is not None else None
                        sold_out = j['props']['pageProps']['properties']['itemDetail']['soldOut']

                        if (inventory is None or 'limitMessage' not in inventory) and sold_out == False:
                            stock = InventoryStatus.IN_STOCK
                        elif sold_out == False and 'limitMessage' in inventory:
                            stock = InventoryStatus.ALMOST_SOLD_OUT
                        elif not sold_out:
                            stock = InventoryStatus.IN_STOCK
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
                                price=delivery_price,
                                type=delivery_type
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
        return "{}_{}_{}".format(self.product_id, self.item_id, self.vendor_item_id)

    @staticmethod
    def getId(item_url: str):
        u = re.search(
            r"products\/(?P<product_id>[\d]+)\?itemId=(?P<item_id>[\d]+).*?(?:|vendorItemId=(?P<vendor_item_id>[\d]+).*)$",
            item_url)

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
