import asyncio
import re
import uuid
from typing import Optional

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import InvalidItemUrlError
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.iherb.const import CODE, NAME
from custom_components.price_tracker.services.iherb.parser import IherbParser
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)

_URL = "https://catalog.app.iherb.com/product/{}"


class IherbEngine(PriceEngine):
    def __init__(
            self,
            item_url: str,
            device: None = None,
            proxies: Optional[list] = None,
            selenium: Optional[str] = None,
            selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = IherbEngine.parse_id(item_url)
        self._proxies = proxies
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData | None:
        request = SafeRequest(
            proxies=self._proxies,
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
        )
        # TODO: Prevent bot captcha
        request.accept_all()
        request.accept_language(language="ko-KR,en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5")
        request.accept_encoding("gzip, deflate, br")
        request.cache_control("no-cache")
        request.keep_alive()
        request.priority_u()
        request.pragma_no_cache()
        request.referer_no_referrer()
        request.sec_fetch_user('?1')
        request.sec_fetch_site('none')
        request.sec_fetch_mode_navigate()
        request.sec_fetch_dest_document()
        request.header(key="Host", value="catalog.app.iherb.com")
        request.header(key="pref",
                       value='{ "storeid": "0", "lac": "ko-KR", "crc": "KRW", "ctc": "KR", "crs": "3", "som": "pounds", "pc": "92571" }')
        request.header(key="x-px-device-model", value="iPhone 14 Pro")
        request.header(key="x-px-mobile-sdk-version", value="3.0.5")
        request.header(key="regiontype", value="GLOBAL")
        request.header(key="appv", value="10.11.1114")
        request.header(key="x-application-id", value="iphoneglobal:10.11.1114:2024111309")
        request.header(key="x-px-authorization", value="")
        request.header(key="x-px-os", value="iOS")
        request.header(key="platform", value="iPhone")
        request.header(key="x-px-os-version", value="18.0")
        request.header(key="x-px-vid", value=str(uuid.uuid4()))
        request.header(key="x-request-id", value=str(uuid.uuid4()).upper())
        request.header(key="x-px-uuid", value=str(uuid.uuid4()))
        request.header(key="x-device-id", value="")
        request.header(key="x-px-device-fp", value=str(uuid.uuid4()).upper())
        request.header(key="ih-exp-user-id", value="")
        request.header(key="traceparent", value="00-")
        request.header(key="ih-experiment",
                       value="eyJjYXRzYiI6eyJFbmREYXRlIjoiMDEvMDEvMjUiLCJDaG9zZW5WYXJpYW50IjoyLCJTb3VyY2UiOjB9LCJocFRpbGUiOnsiRW5kRGF0ZSI6IjAxLzAxLzI1IiwiQ2hvc2VuVmFyaWFudCI6MCwiU291cmNlIjowfSwibmV3cCI6eyJFbmREYXRlIjoiMjAyNC0xMi0yNVQwMDowMDowMFoiLCJDaG9zZW5WYXJpYW50IjoxLCJTb3VyY2UiOjF9LCJhdWciOnsiRW5kRGF0ZSI6IjIwMjUtMDEtMDFUMDA6MDA6MDBaIiwiQ2hvc2VuVmFyaWFudCI6MCwiU291cmNlIjoxfSwiY3NyIjp7IkVuZERhdGUiOiIyMDI1LTAxLTMxVDAwOjAwOjAwWiIsIkNob3NlblZhcmlhbnQiOjIsIlNvdXJjZSI6MX0sImVtcGMiOnsiRW5kRGF0ZSI6IjIwMjUtMDEtMzFUMDA6MDA6MDBaIiwiQ2hvc2VuVmFyaWFudCI6MCwiU291cmNlIjoxfSwiZGFmIjp7IkVuZERhdGUiOiIyMDI0LTEyLTMwVDAwOjAwOjAwWiIsIkNob3NlblZhcmlhbnQiOjMsIlNvdXJjZSI6MX0sInRhbWFyYSI6eyJFbmREYXRlIjoiMjAyNS0wMS0wMVQwMDowMDowMC4wMDBaIiwiQ2hvc2VuVmFyaWFudCI6MCwiU291cmNlIjowfSwicGxwX21vZGVybml6YXRpb25fZW5hYmxlZCI6eyJWYXIiOiIwIiwiRW5kRGF0ZSI6IiIsIlNvdXJjZSI6Mn19")
        request.header(key="ih-pref", value="storeid=0;lc=ko-KR;cc=KRW;ctc=KR;wp=pounds")
        request.cookie(
            key="ih-preference", value="country=KR&language=ko-KR&currency=KRW"
        )
        await request.user_agent(user_agent="iHerbMobile/10.11.1114.2024111309 (iOS 18.0; iPhone15,2; GLOBAL)")
        await request.reuse_session(True)

        response = await request.request(
            method=SafeRequestMethod.GET, url=_URL.format(self.id), retain_cookie=True
        )

        logging_for_response(response, __name__, "iherb")

        if not response.has:
            return None

        parser = IherbParser(data=response.data)

        return ItemData(
            id=self.id_str(),
            brand=parser.brand,
            name=parser.name,
            price=parser.price,
            description=parser.description,
            category=parser.category,
            delivery=parser.delivery,
            unit=parser.unit,
            image=parser.image,
            options=parser.options,
            url=parser.url,
            inventory=parser.inventory_status,
        )

    def id_str(self) -> str:
        return "{}".format(self.id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(r"/(?P<id>\d+)(?:/|)", item_url)

        if u is None:
            raise InvalidItemUrlError("Invalid iherb item url {}".format(item_url))

        g = u.groupdict()

        if g is None:
            raise InvalidItemUrlError("Invalid iherb item url {}".format(item_url))

        return g["id"]

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME

    def url(self) -> str:
        return self.item_url
