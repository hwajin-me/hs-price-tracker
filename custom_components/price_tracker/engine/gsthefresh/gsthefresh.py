from homeassistant.util import aiohttp

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


class GsTheFreshLogin:
    """"""


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
