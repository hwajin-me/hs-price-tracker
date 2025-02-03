import logging
import re
from datetime import datetime
from typing import Optional

from curl_cffi import CurlHttpVersion

from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.error import (
    InvalidItemUrlError,
    NotFoundError,
)
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.services.smartstore.const import NAME, CODE
from custom_components.price_tracker.services.smartstore.parser import SmartstoreParser
from custom_components.price_tracker.utilities.safe_request import (
    SafeRequest,
    SafeRequestMethod,
)
from custom_components.price_tracker.utilities.utils import random_choice, random_bool

_LOGGER = logging.getLogger(__name__)

_URL = "https://{}.naver.com/{}/{}/{}"


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
        request = SafeRequest(
            proxies=self._proxies,
            version=CurlHttpVersion.V2_PRIOR_KNOWLEDGE,
            user_agents=["pc", "mobile"],
        )

        if random_bool():
            await request.request(
                method=SafeRequestMethod.GET,
                url="https://shopping.naver.com/ns/home/today-event",
                max_tries=1,
            )
            request.user_agent(mobile_random=True, pc_random=True)

        if random_bool():
            await request.request(
                method=SafeRequestMethod.GET,
                url="https://shopping.naver.com/ns/home",
                max_tries=1,
            )

        if random_bool():
            await request.request(
                method=SafeRequestMethod.GET,
                url="https://msearch.shopping.naver.com/remote_frame.html",
                max_tries=3,
            )
            await request.request(
                method=SafeRequestMethod.POST,
                url="https://nlog.naver.com/n",
                max_tries=3,
                data={
                    "corp": "naver",
                    "usr": {},
                    "location": "korea_real/korea",
                    "send_ts": datetime.now().timestamp(),
                    "svc": "shopping",
                    "svc_tags": {},
                    "evts": [
                        {
                            "page_url": "https://shopping.naver.com/ns/home",
                            "page_ref": "",
                            "page_id": "08827299cfd39834e5badb487db19f8b",
                            "timing": {
                                "type": "navigate",
                                "unloadEventStart": 0,
                                "unloadEventEnd": 0,
                                "redirectStart": 0,
                                "redirectEnd": 0,
                                "workerStart": 0,
                                "fetchStart": 6.700000286102295,
                                "domainLookupStart": 8.200000286102295,
                                "domainLookupEnd": 9.400000095367432,
                                "connectStart": 9.400000095367432,
                                "secureConnectionStart": 23.90000009536743,
                                "connectEnd": 35.59999990463257,
                                "requestStart": 35.700000286102295,
                                "responseStart": 77.5,
                                "responseEnd": 87.59999990463257,
                                "domInteractive": 319.59999990463257,
                                "domContentLoadedEventStart": 634.2000002861023,
                                "domContentLoadedEventEnd": 634.2000002861023,
                                "domComplete": 0,
                                "loadEventStart": 0,
                                "loadEventEnd": 0,
                                "first_paint": 278.59999990463257,
                                "first_contentful_paint": 278.59999990463257,
                            },
                            "type": "pageview",
                            "page_sti": "shopping",
                            "shp_action_uid": "",
                            "env": {"device_type": "PC Web"},
                            "shp_pagekey": "100410625",
                            "shp": {"contents": {}},
                            "evt_ts": datetime.now().timestamp(),
                        }
                    ],
                    "env": {
                        "os": "MacIntel",
                        "br_ln": "en-US",
                        "br_sr": "1920x1080",
                        "device_sr": "1920x1080",
                        "platform_type": "web",
                        "ch_arch": "arm",
                        "ch_mdl": "",
                        "ch_mob": False,
                        "ch_pltf": "macOS",
                        "ch_ptlfv": "13.1.0",
                        "timezone": "Asia/Seoul",
                        "ch_fvls": [
                            {
                                "brand": "Google Chrome",
                                "version": "131.0.6778.267",
                            },
                            {"brand": "Chromium", "version": "131.0.6778.267"},
                            {"brand": "Not_A Brand", "version": "24.0.0.0"},
                        ],
                    },
                    "tool": {
                        "name": "ntm-web",
                        "ver": "nlogLibVersion=v0.1.40; verName=v2.0.7; ntmVersion=v1.4.1",
                    },
                },
            )

        request.cookie(
            key="NNB",
            value="PPYXCWKWXC"
                  + random_choice(["A", "B", "C", "D", "X"])
                  + random_choice(["A", "B", "C", "D", "E"])
                  + random_choice(["A", "B", "C", "D", "E", "F"]),
        )

        response = await request.request(
            method=SafeRequestMethod.GET,
            url=_URL.format(self.store_type, self.store, self.detail_type, self.product_id),
        )

        if response.is_not_found:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
                http_status=response.status_code,
            )

        text = response.text

        try:
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
                status=ItemStatus.ACTIVE,
            )
        except NotFoundError as e:
            return ItemData(
                id=self.id_str(),
                name="Deleted {}".format(self.id_str()),
                status=ItemStatus.DELETED,
                http_status=response.status_code,
            )
        except Exception as e:
            raise e

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
