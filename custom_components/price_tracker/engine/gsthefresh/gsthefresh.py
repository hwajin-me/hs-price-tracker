from custom_components.price_tracker.const import CONF_GS_NAVER_LOGIN_CODE, CONF_GS_NAVER_LOGIN_FLOW_2_URL, CONF_GS_NAVER_LOGIN_FLOW_3_URL, REQUEST_DEFAULT_HEADERS
from homeassistant.util import aiohttp

import json
import hashlib
from custom_components.price_tracker.engine.data import ItemData
from custom_components.price_tracker.engine.engine import PriceEngine

_UA = "Dart/3.5 (dart:io)"
_REQUEST_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "appinfo_app_version": "5.2.54",
    "appinfo_app_build_number": "1195",
    "appinfo_os_version": "18.0",
    "appinfo_model_name": "iPhone15,2",
    "appinfo_os_type": "ios",
    "appinfo_device_id": "a00000a0fa004cf127333873c60e5b12",
    "device_id": "a00000a0fa004cf127333873c60e5b12"
}
_LOGIN_URL = "https://b2c-bff.woodongs.com/api/bff/v2/auth/accountLogin"

class GsTheFreshLogin:
    """"""
    async def naver_login(code: str, device_id: str) -> str:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.get(url=CONF_GS_NAVER_LOGIN_FLOW_2_URL.format(code)) as response:
                if response.status != 200:
                    raise Exception("Error")
                
                temp_access_token = json.loads(await response.read())['accessToken']
                    
                async with session.post(url=CONF_GS_NAVER_LOGIN_FLOW_3_URL, headers={**REQUEST_DEFAULT_HEADERS, **_REQUEST_HEADERS, 'appinfo_device_id': device_id, 'device_id': device_id, 'authorization': 'Bearer {}'.format(temp_access_token)}) as login:
                    if login.status != 200:
                        raise Exception("Error")
                    
                    j = json.loads(await login.read())

                    if 'data' not in j:
                        raise Exception("parse error")
                    
                    return j['data']['accessToken']

                    
    async def login(device_id: str, username: str, password: str):
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



class GsTheFreshEngine(PriceEngine):


    def __init__(self, item_url: str):
        self.item_url = item_url


    async def load(self) -> ItemData:
        pass


    def id(self) -> str:
        pass

    @staticmethod
    def getId(item_url: str):
        """Get id from short-link"""
        """https://woodongs.com/link?view=gsTheFreshDeliveryDetail&orderType=pickup&itemCode=8712000018948"""
