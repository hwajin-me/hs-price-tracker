from custom_components.price_tracker.const import CONF_GS_NAVER_LOGIN_CODE, CONF_GS_NAVER_LOGIN_FLOW_2_URL, CONF_GS_NAVER_LOGIN_FLOW_3_URL, REQUEST_DEFAULT_HEADERS
from custom_components.price_tracker.device import Device
from custom_components.price_tracker.exception import ApiError, InvalidError
from custom_components.price_tracker.utils import findItem, request, requestPlain

import logging
import aiohttp
import json
import re
import hashlib

from custom_components.price_tracker.engine.data import DeliveryData, DeliveryPayType, ItemData
from custom_components.price_tracker.engine.engine import PriceEngine

_UA = "Dart/3.5 (dart:io)"
_REQUEST_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "appinfo_app_version": "5.2.54",
    "appinfo_app_build_number": "1195",
    "appinfo_os_version": "18.0",
    "appinfo_model_name": "iPhone15,2",
    "appinfo_os_type": "ios",
    "appinfo_device_id": "a00000a0fa004cf127333873c60e5b12",
    "device_id": "a00000a0fa004cf127333873c60e5b12"
}
_LOGIN_URL = "https://b2c-bff.woodongs.com/api/bff/v2/auth/accountLogin"
_REAUTH_URL = "https://b2c-apigw.woodongs.com/auth/v1/token/reissue" 
_PRODUCT_URL = "https://b2c-apigw.woodongs.com/supermarket/v1/wdelivery/item/{}"
_ITEM_LINK = "https://woodongs.com/link?view=gsTheFreshDeliveryDetail&orderType=pickup&itemCode={}"

_LOGGER = logging.getLogger(__name__)

class GsTheFreshLogin:
    """"""
    async def naver_login(self, code: str, device_id: str) -> str:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.get(url=CONF_GS_NAVER_LOGIN_FLOW_2_URL.format(code), headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS}) as response:
                if response.status != 200:
                    raise Exception("GS THE FRESH - NAVER Response Error")
                naver_response = await response.read()
                temp_access_token = json.loads(naver_response)['access_token']
                    
                async with session.post(url=CONF_GS_NAVER_LOGIN_FLOW_3_URL, headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS, 'device_id': device_id, 'appinfo_device_id': device_id, 'Authorization': 'Bearer {}'.format(temp_access_token), 'content-type': 'application/json'}, json={'socialType': 'naver'}) as login:
                    if login.status != 200:
                        raise Exception("GS THE FRESH - Authentication Error {}".format(login))
                    
                    j = json.loads(await login.read())

                    if 'data' not in j:
                        raise Exception("parse error")
                    
                    return {
                        'access_token': j['data']['accessToken'],
                        'refresh_token': j['data']['refreshToken'],
                        'name': j['data']['customer']['customerName'],
                        'number':  j['data']['customer']['customerNumber'],
                    }

                    
    async def login(self, device_id: str, username: str, password: str):
        sha256 = hashlib.sha256()
        sha256.update(password.encode())
        hash_password = sha256.hexdigest()
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.post(url=_LOGIN_URL, json={
                'id': username,
                'password': hash_password
            }, headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS, 'device_id': device_id, 'appinfo_device_id': device_id}) as response:
                if response.status != 200:
                    raise Exception('')
                
                j = json.loads(await response.read())

                return {
                    'access_token': j['data']['accessToken'],
                    'refresh_token': j['data']['refreshToken'],
                    'name': j['data']['customer']['customerName'],
                    'number':  j['data']['customer']['customerNumber'],
                }


    async def reauth(self, device_id: str, access_token: str) -> str:
        response = await request(_REAUTH_URL, headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS, 'appinfo_device_id': device_id, 'device_id': device_id,  'authorization': 'Bearer {}'.format(access_token)})
        
        if 'data' in response:
            j = json.loads(response['data'])

            return {
                'access_token': j['data']['accessToken'],
                'refresh_token': j['data']['refreshToken'],
                'name': j['data']['customer']['customerName'],
                'number':  j['data']['customer']['customerNumber'],
            }
        else:
            raise ApiError('GS THE FRESH Login(reauthentication) Error')


class GsTheFreshEngine(PriceEngine):


    def __init__(self, item_url: str):
        self.item_url = item_url


    async def load(self) -> ItemData:
        result = await request(_PRODUCT_URL.format(self.item_url), headers={**_REQUEST_HEADERS})
        response = json.loads(result)

        if 'data' not in response or 'weDeliveryItemDetailResultList' not in response['data'] or len(response['data']['weDeliveryItemDetailResultList']) < 1:
            raise ApiError('GS THE FRESH Response error')
        
        data = response['data']['weDeliveryItemDetailResultList']
        id = data['itemCode']
        name = data['indicateItemName']
        description = data['itemNotification']
        quantity = data['stockQuantity']
        image = data['weDeliveryItemImageUrl']
        price = data['normalSalePrice']
        sold_out = data['soldOutYn']
        url = _ITEM_LINK.format(id)

        delivery_data = response['data']['processingDeliveryAmountResultList']
        if delivery_data is not None and len(delivery_data) > 0:
            delivery_price = findItem(delivery_data, 'commonCode', 3)
            if delivery_price is not None and delivery_price > 0:
                delivery = DeliveryData(price=delivery_price, type = DeliveryPayType.PAID)
            else:
                delivery = DeliveryData(price=0, type = DeliveryPayType.FREE)
        else:
            delivery = DeliveryData(price=0, type = DeliveryPayType.FREE)

        return ItemData(
            id = id,
            name = name,
            price = price,
            delivery=delivery
        )

    def id(self) -> str:
        pass

    @staticmethod
    def getId(item_url: str):
        """Get id from short-link"""
        """https://woodongs.com/link?view=gsTheFreshDeliveryDetail&orderType=pickup&itemCode=8712000018948"""
        response = requests(url=item_ur, allow_redirects=False)
        loc = response.headers['location']

        if loc is None:
            raise InvalidError('GS THE FRESH Item ID Parse(Request) Error')
        
        u = re.search(r'itemCode=(?P<product_id>[\d]+)', loc)
        g = u.groupdict()

        if g is None:
            raise InvalidError('GS THE FRESH Item ID Parse(Regex) Error')

        return g['product_id']

class GsTheFreshDevice(Device):
    """"""

    def __init__(self, device_id: str, access_token: str, refresh_token: str, name: str, number: str):
        super().__init__("{}_{}_{}".format(device_id, name, number))
        self._device_id = device_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._name = name
        self._number = number