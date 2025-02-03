import asyncio
import dataclasses
import json
import logging
import random
from enum import Enum
from typing import Optional, Callable, Self, Awaitable

import fake_useragent
from curl_cffi import requests, CurlHttpVersion, CurlSslVersion
from curl_cffi.requests import Cookies
from voluptuous import default_factory

from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


class SafeRequestError(Exception):
    pass


class CustomSessionCookie(Cookies):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def extract_cookies(self, response, request):
        return self.jar.extract_cookies(response, request)


class CustomAsyncSession(requests.AsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_fp = {
            "tls_min_version": CurlSslVersion.TLSv1_2,
        }


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
    def is_not_found(self):
        return self.status_code == 404

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
        method: SafeRequestMethod,
        url: str,
        data: dict,
        proxy: str,
        timeout: int,
        session: requests.AsyncSession,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ) -> SafeRequestResponseData:
        pass


class SafeRequestEngineCurlCffi(SafeRequestEngine):
    def __init__(
        self,
        impersonate: str = "chrome124",
        version: Optional[CurlHttpVersion] = CurlHttpVersion.V2TLS,
    ):
        self._impersonate = impersonate
        self._version = version

    async def request(
        self,
        method: SafeRequestMethod,
        url: str,
        data: dict,
        proxy: str,
        timeout: int,
        session: requests.AsyncSession,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ) -> SafeRequestResponseData:
        response = await session.request(
            method=method.name.upper(),
            url=url,
            headers=headers,
            json=data,
            data=data,
            cookies=cookies,
            proxy=proxy,
            timeout=timeout,
            allow_redirects=True,
            default_headers=True,
            verify=True,
            http_version=self._version,
            impersonate=self._impersonate,
        )

        data = response.text
        cookies = response.cookies
        access_token = (
            response.headers.get("Authorization").replace("Bearer ", "")
            if response.headers.get("Authorization") is not None
            else None
        )

        if response.status_code > 399 and response.status_code != 404:
            raise SafeRequestError(
                f"Failed to request (curl-cffi) {url} with status code {response.status_code}"
            )

        return SafeRequestResponseData(
            data=data,
            status_code=response.status_code,
            cookies=cookies,
            access_token=access_token,
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
        impersonate: str = "chrome124",
        version: Optional[CurlHttpVersion] = CurlHttpVersion.V2TLS,
        user_agents: list[str] = None,
    ):
        if headers is not None:
            self._headers = headers
        else:
            self._headers = {}

        self._headers = {
            "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Pragma": "no-cache",
            **self._headers,
        }
        self._ua_platforms = (
            user_agents if user_agents is not None else ["pc", "mobile"]
        )
        self._timeout = 25
        self._proxies: list[str] = proxies if proxies is not None else []
        self._cookies: dict = cookies if cookies is not None else {}
        self._selenium = selenium
        self._selenium_proxy = selenium_proxy
        self._chains: list[SafeRequestEngine] = []
        self._impersonate = impersonate
        self._version = version

        self._chains = self._chains + (
            [
                SafeRequestEngineCurlCffi(
                    impersonate=self._impersonate,
                    version=version,
                ),
            ]
            if chains is None
            else chains
        )

    def impersonate(self, impersonate: str):
        """"""
        self._impersonate = impersonate

        return self

    def accept_text_html(self):
        """"""
        self._headers["Accept"] = (
            "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        )

        return self

    def accept_almost_all(self):
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

    def clear_header(self):
        self._headers = {}
        return self

    def user_agent(
        self,
        user_agent: Optional[str] | list = None,
        mobile_random: bool = False,
        pc_random: bool = False,
    ):
        """"""
        if user_agent is not None:
            self._ua_platforms = []
            if isinstance(user_agent, list):
                self._headers["User-Agent"] = random.choice(user_agent)
            else:
                self._headers["User-Agent"] = user_agent
            return self

        if mobile_random:
            self._ua_platforms.append("mobile")
        if pc_random:
            self._ua_platforms.append("pc")
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
        if key is None and value is None and data is None and item is None:
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
        timeout: int = 25,
        raise_errors: bool = False,
        max_tries: int = 8,
        post_try_callables: list[Callable[[Self], Awaitable[None]]] = None,
        retain_cookie=True,
    ) -> SafeRequestResponseData:
        errors = []
        return_data = SafeRequestResponseData()

        async with CustomAsyncSession(
            impersonate=self._impersonate, http_version=self._version
        ) as session:
            for tries in range(max_tries):
                if tries >= max_tries:
                    return return_data

                for chain in self._chains:
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

                    if bool(self._headers):
                        if len(self._ua_platforms) > 0:
                            ua_engine = await asyncio.to_thread(
                                fake_useragent.UserAgent, platforms=self._ua_platforms
                            )

                            self._headers["User-Agent"] = ua_engine.random

                    try:
                        return_data = await chain.request(
                            headers=self._headers if bool(self._headers) else None,
                            method=method,
                            url=url,
                            data=data,
                            proxy=proxy,
                            timeout=timeout,
                            session=session,
                            cookies=self._cookies,
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
                        errors.append(e)
                        pass
                    finally:
                        tries += 1

        if len(errors) > 0 and raise_errors:
            _LOGGER.error(f"Failed to request {url}, {set(Lu.map(errors, lambda x: repr(x)))}")
            raise errors[0]
        else:
            _LOGGER.error("Request failed %s", errors)

        return return_data
