import json
import logging
import re

import aiohttp

from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.engine.data import ItemData, ItemUnitType, ItemUnitData, InventoryStatus, \
    DeliveryData
from custom_components.price_tracker.engine.engine import PriceEngine

_LOGGER = logging.getLogger(__name__)

_URL = 'https://m.coupang.com/vm/v5/'
_ITEM_LINK = 'https://www.coupang.com/vp/products/{}?vendorItemId={}'


class CoupangEngine(PriceEngine):
    def __init__(self, item_url: str):
        self.item_url = item_url
        data = CoupangEngine.getId(item_url)

        self.product_id = data['product_id']
        self.vendor_item_id = data['vendor_item_id']

    async def load(self) -> ItemData:
        if self.vendor_item_id:
            url = _URL + 'products/' + self.product_id + '/vendor-items/' + self.vendor_item_id
        else:
            url = _URL + 'enhanced-pdp/products/' + self.product_id

        data = {}

        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url, headers={**REQUEST_DEFAULT_HEADERS,
                                                     'Cookie': 'sid=1; PCID=2; x-coupang-accept-language=ko-KR; x-coupang-target-market=KR; helloCoupang=Y;'}) as response:
                    result = await response.read()
                    if response.status == 200:
                        _LOGGER.debug("Coupang Response: %s", result)

                        j = json.loads(result)
                        if 'vendorItemDetail' in j['rData']:
                            info = j['rData']['vendorItemDetail']['item']
                        elif 'item' in j['rData']:
                            info = j['rData']['item']

                        if ('couponPrice' in info) and info['couponPrice']:
                            price = info['couponPrice']
                        else:
                            price = info['salePrice']

                        if 'unitPrice' in info:
                            data['unit_price'] = info['unitPrice']
                            u = re.match(r"^(?P<per>[\d,]+)(?P<unit_type>g|개|ml|kg|l)당 (?P<price>[\d,]+)원$",
                                         info['unitPrice'])
                            g = u.groupdict()
                            data['unit_type'] = g['unit_type']
                            data['unit_per'] = float(g['per'].replace(',', ''))
                            data['unit_each_price'] = float(g['price'].replace(',', ''))
                            if g['unit_type'] == 'g' and int(g['per'].replace(',', '')) == 10:
                                data['unit_each_price'] = float(g['price'].replace(',', '')) * 10
                                data['unit_per'] = float(g['per'].replace(',', '')) * 10
                            if g['unit_type'] == 'ml' and int(g['per'].replace(',', '')) == 10:
                                data['unit_each_price'] = float(g['price'].replace(',', '')) * 10
                                data['unit_per'] = float(g['per'].replace(',', '')) * 10
                            unit_price = ItemUnitData(
                                unit_type=ItemUnitType.of(g['unit_type']),
                                unit=float(g['per'].replace(',', '')),
                                price=float(g['price'].replace(',', ''))
                            )

                        stock = InventoryStatus.IN_STOCK if info[
                                                                'buyableQuantity'] >= 10 else InventoryStatus.ALMOST_SOLD_OUT if \
                            info['buyableQuantity'] > 0 else InventoryStatus.OUT_OF_STOCK

                        return ItemData(
                            id="{}/{}".format(info['productId'], info['vendorItemId']),
                            price=price,
                            name=info['productName'],
                            description=info['itemName'],
                            url=_ITEM_LINK.format(info['productId'],
                                                  info['vendorItemId']),
                            image=j['rData']['resource']['originalSquare']['url'],
                            delivery=DeliveryData(
                                price=float(info['deliveryCharge']),
                            ),
                            unit=unit_price,
                            category=info['categoryId'],
                            inventory=stock,
                        )
        except:
            _LOGGER.exception("Coupang Parse Error")

    def id(self) -> str:
        return "{}_{}".format(self.product_id, self.vendor_item_id)

    @staticmethod
    def getId(item_url: str):
        u = re.search(r"products\/(?P<product_id>[\d]+).*?(?:|vendorItemId=(?P<vendor_item_id>[\d]+).*)$", item_url)

        if u is None:
            raise Exception("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data['product_id'] = g['product_id']
        data['vendor_item_id'] = ''
        if 'vendor_item_id' in g:
            data['vendor_item_id'] = g['vendor_item_id']
        return data
