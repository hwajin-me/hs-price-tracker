import datetime
import logging
import re
from typing import Optional
from urllib.parse import urlencode
from uuid import uuid4

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
)
from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.services.smartstore.const import NAME, CODE
from custom_components.price_tracker.services.smartstore.parser import SmartstoreParser
from custom_components.price_tracker.utilities.hash import md5
from custom_components.price_tracker.utilities.logs import logging_for_response
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
    SafeRequestEngineRequests,
    SafeRequestEngineCloudscraper,
    SafeRequestEngineAiohttp,
    bot_agents, SafeRequestEngineHttpx,
)
from custom_components.price_tracker.utilities.utils import random_bool

_LOGGER = logging.getLogger(__name__)

_URL = "https://m.{}.naver.com/{}/{}/{}"


class SmartstoreEngine(PriceEngine):
    def __init__(
            self,
            item_url: str,
            device: None = None,
            proxies: Optional[list] = None,
            selenium: Optional[str] = None,
            selenium_proxy: Optional[list] = None,
    ):
        self.item_url = item_url
        self.id = SmartstoreEngine.parse_id(item_url)
        self.store_type = self.id["store_type"]
        self.detail_type = self.id["detail_type"]
        self.store = self.id["store"]
        self.product_id = self.id["product_id"]
        self._proxies = proxies
        self._device = device
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy

    async def load(self) -> ItemData | None:
        url = _URL.format(
            self.store_type, self.store, self.detail_type, self.product_id
        )
        request = SafeRequest(
            chains=[
                SafeRequestEngineRequests(),
                SafeRequestEngineCloudscraper(),
                SafeRequestEngineAiohttp(),
                SafeRequestEngineHttpx(),
            ],
            proxies=self._proxies,
            selenium=self._selenium,
            selenium_proxy=self._selenium_proxy,
        )
        request.accept_text_html()
        if random_bool():
            request.accept_all()
        request.accept_language(
            language="en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5"
        )
        request.accept_encoding("gzip, zlib, deflate, zstd, br")
        request.content_type()
        request.referer(referer="https://m.shopping.naver.com/cart?pageExitType-=recommend")
        request.sec_fetch_dest_document()
        request.sec_fetch_mode_navigate()
        request.sec_fetch_site(site="same-site")
        request.cookie(key="smartstore-STORE_LAST_VISITED_DATETIME",
                       value=str(datetime.datetime.timestamp(datetime.datetime.now())))
        request.cookie(key="NA_CO", value=str(urlencode(query="ck=m42vmvdk|ci=|tr=mrec|hk=|trx=undefined")))
        request.cookie(key="wcs_bt", value="s_1:")
        request.cookie(key="DA_DD", value=str(uuid4()))
        request.cookie(key="NID_SES", value="")
        request.cookie(key="BUC", value="")
        request.cookie(key="_ga", value="")
        request.cookie(key="_fwb", value="")
        request.cookie(key="NFS", value="2")
        request.cookie(key="BNB_FINANCE_HOME_TOOLTIP_PAYMENT", value="true")
        request.cookie(key="MM_NEW", value="2")
        request.cookie(key="NID_AUT", value="")
        request.cookie(key="GDOT", value="Y")
        request.cookie(key="NACT", value="1")
        request.cookie(key="nstore_session", value="")
        request.cookie(key="nstore_pagesession", value="")
        request.cookie(key="NV_WETR_LAST_ACCESS_RGN_M", value="MDkyMDA2NzE=")
        request.cookie(key="NV_WETR_LOCATION_RGN_M", value="MDkyMDA2NzE=")
        request.cookie(key="ab.storage.deviceId.{}".format(str(uuid4())),
                       value="g|{}|e:undefined|c:{}|l:{}".format(str(uuid4()), str(datetime.datetime.timestamp(
                           datetime.datetime.now()
                       )),
                                                                 str(datetime.datetime.timestamp(
                                                                     datetime.datetime.now()))))
        request.cookie(key="ASID", value=md5(datetime.datetime.now().isoformat()))

        if random_bool():
            request.accept_encoding("gzip, deflate")

        # If brand store type
        if self.store_type == "brand":
            await request.user_agent(mobile_random=True, pc_random=True)
            request.keep_alive()
        else:
            await request.user_agent(
                user_agent="Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
            )

        # Random logics for selenium proxy
        if self._selenium and self._selenium_proxy:
            await request.user_agent(user_agent=bot_agents())

        response = await request.request(
            method=SafeRequestMethod.GET,
            url=url,
        )

        if not response.has:
            return None

        text = response.text

        logging_for_response(response=text, name=__name__, domain="smartstore")

        naver_parser = SmartstoreParser(data=text)

        return ItemData(
            id=self.id_str(),
            price=naver_parser.price,
            name=naver_parser.name,
            description=naver_parser.description,
            category=naver_parser.category,
            image=naver_parser.image,
            url=naver_parser.url,
            inventory=naver_parser.inventory_status,
            delivery=naver_parser.delivery,
            options=naver_parser.options,
        )

    def id_str(self) -> str:
        return "{}_{}".format(self.store, self.product_id)

    @staticmethod
    def parse_id(item_url: str):
        u = re.search(
            r"(?P<store_type>smartstore|shopping|brand)\.naver\.com/(?P<store>[a-zA-Z\d\-_]+)/(?P<detail_type>products|\w+)/(?P<product_id>\d+)",
            item_url,
        )

        if u is None:
            raise InvalidItemUrlError("Bad item_url " + item_url)
        data = {}
        g = u.groupdict()
        data["store_type"] = g["store_type"]
        data["detail_type"] = g["detail_type"]
        data["store"] = g["store"]
        data["product_id"] = g["product_id"]

        return data

    @staticmethod
    def engine_code() -> str:
        return CODE

    @staticmethod
    def engine_name() -> str:
        return NAME
