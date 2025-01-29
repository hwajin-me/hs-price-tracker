import asyncio
import dataclasses
import json
import logging
import random
import ssl
from enum import Enum
from typing import Optional, Callable, Self, Awaitable

import cloudscraper
import fake_useragent
import urllib3
from curl_cffi import requests, CurlHttpVersion
from curl_cffi.requests import AsyncSession, Cookies
from voluptuous import default_factory

from custom_components.price_tracker.utilities.list import Lu


def bot_agents():
    return ["NaverBot", "Yeti", "Googlebot-Mobile", "HTTPie/3.2.4"]


def ssl_context():
    ctx = ssl.SSLContext()

    return ctx


_LOGGER = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SafeRequestError(Exception):
    pass


class CustomSessionCookie(Cookies):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def extract_cookies(self, response, request):
        return self.jar.extract_cookies(response, request)


class CustomSession(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug = True
        self.trust_env = True
        if kwargs.get("cookies") is not None:
            self.cookies = CustomSessionCookie(kwargs.get("cookies"))
        else:
            self.cookies = CustomSessionCookie()


@dataclasses.dataclass
class SafeRequestResponseData:
    data: Optional[str] = default_factory("")
    status_code: int = default_factory(400)
    access_token: Optional[str] = default_factory(None)
    cookies: dict = default_factory({})

    def __init__(
            self,
            data: Optional[str] = None,
            status_code: int = None,
            cookies=None,
            access_token: Optional[str] = None,
    ):
        if cookies is None:
            cookies = {}
        self.data = data
        self.status_code = status_code
        self.cookies = cookies
        self.access_token = access_token

    @property
    def text(self):
        return self.data

    @property
    def has(self):
        return (
                self.status_code is not None
                and self.status_code <= 399
                and self.data is not None
                and self.data != ""
        )

    @property
    def json(self):
        try:
            return json.loads(self.data)
        except json.JSONDecodeError:
            return None


class SafeRequestMethod(Enum):
    POST = "post"
    GET = "get"
    PUT = "put"
    DELETE = "delete"


class SafeRequestEngine:
    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict,
            proxy: str,
            timeout: int,
    ) -> SafeRequestResponseData:
        pass


class SafeRequestEngineAiohttp(SafeRequestEngine):
    def __init__(
            self,
            impersonate: str = "chrome",
            session: Optional[requests.Session] = None,
    ):
        self._impersonate = impersonate
        if session is not None:
            self._session = session
        else:
            self._session = CustomSession(
                impersonate=impersonate, http_version=CurlHttpVersion.V2TLS
            )

    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict,
            proxy: str,
            timeout: int,
    ) -> SafeRequestResponseData:
        async with AsyncSession() as session:
            response = await session.request(
                method=method.name.upper(),
                url=url,
                headers=headers,
                json=data,
                data=data,
                proxy=proxy,
                timeout=timeout,
                allow_redirects=True,
                http_version=CurlHttpVersion.V2TLS,
                impersonate=self._impersonate,
            )

            data = response.text
            cookies = response.cookies
            access_token = (
                response.headers.get("Authorization").replace("Bearer ", "")
                if response.headers.get("Authorization") is not None
                else None
            )
            if response.status_code > 399:
                raise SafeRequestError(
                    f"Failed to request {url} with status code {response.status_code}"
                )
            return SafeRequestResponseData(
                data=data,
                status_code=response.status_code,
                cookies=cookies,
                access_token=access_token,
            )


class SafeRequestEngineRequests(SafeRequestEngine):
    def __init__(
            self,
            impersonate: str = "chrome",
            session: Optional[requests.Session] = None
    ):
        self._impersonate = impersonate
        if session is not None:
            self._session = session
        else:
            self._session = CustomSession(
                impersonate=impersonate, http_version=CurlHttpVersion.V2TLS
            )

    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict,
            proxy: str,
            timeout: int,
    ) -> SafeRequestResponseData:
        response = await asyncio.to_thread(
            requests.request,
            method=method.name.upper(),
            url=url,
            headers=headers,
            data=data,
            proxies={
                "http": proxy,
                "https": proxy,
            }
            if proxy is not None
            else None,
            timeout=timeout,
            allow_redirects=True,
            default_headers=True,
            impersonate=self._impersonate,
            http_version=CurlHttpVersion.V2TLS,
        )

        if response.status_code > 399 and response.status_code != 404:
            raise SafeRequestError(
                f"Failed to request {url} with status code {response.status_code}"
            )

        return SafeRequestResponseData(
            data=response.text,
            status_code=response.status_code,
            cookies=response.cookies.get_dict(),
            access_token=response.headers.get("Authorization").replace("Bearer ", "")
            if response.headers.get("Authorization") is not None
            else None,
        )


class SafeRequestEngineCloudscraper(SafeRequestEngine):
    def __init__(
            self,
            impersonate: str = "chrome",
            session: Optional[requests.Session] = None
    ):
        self._impersonate = impersonate
        if session is not None:
            self._session = session
        else:
            self._session = CustomSession(
                impersonate=impersonate, http_version=CurlHttpVersion.V2TLS
            )

    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: any,
            proxy: str,
            timeout: int,
    ) -> SafeRequestResponseData:
        scraper = await asyncio.to_thread(
            cloudscraper.create_scraper,
            sess=self._session,
        )
        response = await asyncio.to_thread(
            scraper.request,
            method=method.name.lower(),
            url=url,
            headers=headers,
            json=data,
            proxies={
                "http": proxy,
                "https": proxy,
            }
            if proxy is not None
            else None,
            timeout=timeout,
            allow_redirects=True,
        )
        if response.status_code > 399 and response.status_code != 404:
            raise SafeRequestError(
                f"Failed to request {url} with status code {response.status_code}"
            )

        return SafeRequestResponseData(
            data=response.text,
            status_code=response.status_code,
            cookies=response.cookies.get_dict(),
            access_token=response.headers.get("Authorization").replace("Bearer ", "")
            if response.headers.get("Authorization") is not None
            else None,
        )


class SafeRequest:
    def __init__(
            self,
            chains: list[SafeRequestEngine] = None,
            proxies: list[str] = None,
            cookies: dict = None,
            headers: dict = None,
            selenium: Optional[str] = None,
            selenium_proxy: Optional[list[str]] = None,
            impersonate: str = "chrome",
            session: Optional[requests.Session] = None,
    ):
        if headers is not None:
            self._headers = headers
        else:
            self._headers = {}
        self._headers = {
            "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/json",
            "Connection": "close",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Priority": "u=0, i",
            "Pragma": "no-cache",
            **self._headers,
        }
        self._timeout = 60
        self._proxies: list[str] = proxies if proxies is not None else []
        self._cookies: dict = cookies if cookies is not None else {}
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy
        self._chains: list[SafeRequestEngine] = []
        self._impersonate = impersonate
        if session is not None:
            self._session = session
        else:
            self._session = CustomSession(
                impersonate=impersonate, http_version=CurlHttpVersion.V2TLS
            )

        self._chains = self._chains + (
            [
                SafeRequestEngineCloudscraper(
                    impersonate=impersonate,
                    session=session
                ),
                SafeRequestEngineAiohttp(
                    impersonate=impersonate,
                    session=session
                ),
                SafeRequestEngineRequests(
                    impersonate=impersonate,
                    session=session
                ),
            ]
            if chains is None
            else chains
        )

    def accept_text_html(self):
        """"""
        self._headers["Accept"] = (
            "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        )

        return self

    def accept_all(self):
        """"""
        self._headers["Accept"] = "*/*"

        return self

    def accept_language(self, language: str = None, is_random: bool = False):
        """"""
        if is_random:
            languages = [
                "en-US",
                "en-US,en;q=0.9",
                "en-US,en;q=0.9,ko;q=0.8",
                "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7",
                "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6",
                "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5",
                "en",
                "ko",
                "ko-KR",
            ]
            self._headers["Accept-Language"] = random.choice(languages)
        elif language is not None:
            self._headers["Accept-Language"] = language

        return self

    def accept_encoding(self, encoding: str):
        """"""
        self._headers["Accept-Encoding"] = encoding

        return self

    async def user_agent(
            self,
            user_agent: Optional[str] | list = None,
            mobile_random: bool = False,
            pc_random: bool = False,
    ):
        """"""
        if user_agent is not None:
            if isinstance(user_agent, list):
                self._headers["User-Agent"] = random.choice(user_agent)
            else:
                self._headers["User-Agent"] = user_agent
            return self

        platforms = []
        if mobile_random:
            platforms.append("mobile")
        if pc_random:
            platforms.append("pc")
        ua_engine = await asyncio.to_thread(
            fake_useragent.UserAgent, platforms=platforms
        )
        self._headers["User-Agent"] = ua_engine.random

        if mobile_random:
            self._headers["Sec-Ch-Ua-Mobile"] = "?0"

        return self

    def chains(self, chains: list[SafeRequestEngine]):
        """"""
        self._chains = chains

        return self

    def auth(self, token: Optional[str]):
        """"""
        if token is not None:
            self._headers["Authorization"] = f"Bearer {token}"
        else:
            self._headers.pop("Authorization", None)

        return self

    def connection(self, connection: str):
        """"""
        self._headers["Connection"] = connection

    def keep_alive(self):
        """"""
        self._headers["Connection"] = "keep-alive"

    def connection_type(self, connection_type: str):
        """"""
        self._headers["Connection"] = connection_type

        return self

    def content_type(self, content_type: str | None = None):
        """"""
        if content_type is None:
            self._headers.pop("Content-Type", None)
        else:
            self._headers["Content-Type"] = content_type

        return self

    def cache_control(self, cache_control: str):
        """"""
        self._headers["Cache-Control"] = cache_control

        return self

    def host(self, host: str):
        """"""
        self._headers["Host"] = host

        return self

    def cache_control_no_cache(self):
        """"""
        self._headers["Cache-Control"] = "no-cache"

        return self

    def sec_fetch_dest(self, sec_fetch_dest: str):
        """"""
        self._headers["Sec-Fetch-Dest"] = sec_fetch_dest

        return self

    def sec_fetch_dest_document(self):
        """"""
        self._headers["Sec-Fetch-Dest"] = "document"

        return self

    def sec_fetch_mode(self, sec_fetch_mode: str):
        """"""
        self._headers["Sec-Fetch-Mode"] = sec_fetch_mode

        return self

    def sec_fetch_mode_navigate(self):
        """"""
        self._headers["Sec-Fetch-Mode"] = "navigate"

        return self

    def sec_fetch_user(self, user):
        """"""
        self._headers["Sec-Fetch-User"] = user

        return self

    def sec_fetch_site(self, site):
        """"""
        self._headers["Sec-Fetch-Site"] = site

        return self

    def priority(self, priority: str):
        """"""
        self._headers["Priority"] = priority

        return self

    def priority_u(self):
        """"""
        self._headers["Priority"] = "u=0, i"

        return self

    def pragma(self, pragma: str):
        """"""
        self._headers["Pragma"] = pragma

        return self

    def pragma_no_cache(self):
        """"""
        self._headers["Pragma"] = "no-cache"

        return self

    def referer(self, referer: str):
        """"""
        self._headers["Referer"] = referer

        return self

    def referer_no_referrer(self):
        """"""
        self._headers["Referer"] = "no-referrer"

        return self

    def sec_ch_ua(self, sec_ch_ua: str):
        """"""
        self._headers["Sec-Ch-Ua"] = sec_ch_ua

        return self

    def sec_ch_ua_mobile(self):
        """"""
        self._headers["Sec-Ch-Ua-Mobile"] = "?0"

        return self

    def sec_ch_ua_platform(self, sec_ch_ua_platform: str):
        """"""
        self._headers["Sec-Ch-Ua-Platform"] = sec_ch_ua_platform

        return self

    def timeout(self, seconds: int):
        """"""
        self._timeout = seconds

        return self

    def header(self, key: str, value: str):
        """"""
        self._headers[key] = value

        return self

    def headers(self, headers: dict):
        """"""
        self._headers = {**self._headers, **headers}

        return self

    def remove_headers(self, excepts: list[str] = None):
        """"""
        if excepts is not None:
            self._headers = {k: v for k, v in self._headers.items() if k in excepts}
        else:
            self._headers = {}

        return self

    def proxy(self, proxy: str | None = None):
        """"""
        if proxy is None:
            self._proxies = []
        else:
            self._proxies.append(proxy)

        return self

    async def reuse_session(self, flag=True):
        if flag:
            self._session = await asyncio.to_thread(requests.Session)
        else:
            self._session = None

    def proxies(self, proxies: list[str] | str | None):
        """"""
        if isinstance(proxies, list):
            self._proxies = proxies
        elif isinstance(proxies, str):
            self._proxies = Lu.map([proxies.split(",")], lambda x: x.strip())
        else:
            self._proxies = []

        return self

    def cookie(
            self, key: str = None, value: str = None, data: str = None, item: dict = None
    ):
        """"""
        if key is not None and value is not None and data is None and item is None:
            return self

        if data is not None:
            self._cookies = {
                **self._cookies,
                **Lu.map(data.split(";"), lambda x: x.split("=")).to_dict(),
            }
        elif item is not None:
            self._cookies = {**self._cookies, **item}
        else:
            self._cookies[key] = value

        return self

    async def request(
            self,
            url: str,
            method: SafeRequestMethod = SafeRequestMethod.GET,
            data: any = None,
            timeout: int = 60,
            raise_errors: bool = False,
            max_tries: int = 10,
            post_try_callables: list[Callable[[Self], Awaitable[None]]] = None,
            retain_cookie=False,
    ) -> SafeRequestResponseData:
        errors = []
        tries = 0
        return_data = SafeRequestResponseData()

        for chain in self._chains:
            await asyncio.sleep(random.randrange(1, 2))

            if tries >= max_tries:
                return return_data

            if tries > 0 and post_try_callables is not None:
                for callable_ in post_try_callables:
                    await callable_(self)

            proxy = (
                random.choice(self._proxies + [None])
                if len(self._proxies) > 0
                else None
            )

            headers = {
                **self._headers,
                "Host": url.split("/")[2]
                if "Host" not in self._headers
                else self._headers["Host"],
            }
            if self._cookies and len(self._cookies) > 0:
                headers["Cookie"] = "; ".join(
                    [f"{k}={v}" for k, v in self._cookies.items()]
                )

            try:
                return_data = await chain.request(
                    headers=headers,
                    method=method,
                    url=url,
                    data=data,
                    proxy=proxy,
                    timeout=timeout,
                )

                if return_data.status_code <= 399 or retain_cookie:
                    self.cookie(item=return_data.cookies)

                _LOGGER.debug(
                    "Safe request success with %s [%s] (%s) [Proxy: %s] <%s>",
                    chain.__class__.__name__,
                    method.name,
                    url,
                    proxy,
                    self._cookies,
                )

                return return_data
            except Exception as e:
                _LOGGER.error(
                    f"Failed to request {url}, [Proxy: {proxy}] with {chain.__class__.__name__}: {e}"
                )
                errors.append(e)
                pass
            finally:
                tries += 1

        if len(errors) > 0 and raise_errors:
            raise errors[0]
        else:
            _LOGGER.debug("Safe request silently failed %s", errors)

        return return_data
