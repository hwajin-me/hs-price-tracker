import asyncio
import dataclasses
import logging
import random
import ssl
from enum import Enum
from typing import Optional, Callable

import aiohttp
import cloudscraper
import fake_useragent
import httpx
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from voluptuous import default_factory
from webdriver_manager.chrome import ChromeDriverManager

import requests
from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxyfacade import (
    SafeRequestProxyFacade,
)
from custom_components.price_tracker.utilities.utils import random_bool

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

_LOGGER = logging.getLogger(__name__)


class SafeRequestError(Exception):
    pass


@dataclasses.dataclass
class SafeRequestResponseData:
    data: Optional[str] = default_factory("")
    status_code: int = default_factory(400)
    access_token: Optional[str] = default_factory(None)
    cookies: dict = default_factory({})

    def __init__(
        self,
        data: Optional[str] = None,
        status_code: int = 400,
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
    async def request(
        self,
        headers: dict,
        method: SafeRequestMethod,
        url: str,
        data: dict,
        proxy: str,
        timeout: int,
    ) -> SafeRequestResponseData:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method.name.lower(),
                url=url,
                headers=headers,
                json=data,
                proxy=proxy,
                timeout=timeout,
                allow_redirects=True,
                auto_decompress=True,
                max_line_size=99999999,
                read_bufsize=99999999,
                compress=False,
                read_until_eof=True,
                expect100=True,
                chunked=False,
                ssl=ctx,
                verify_ssl=False,
            ) as response:
                data = await response.text()
                cookies = response.cookies
                access_token = (
                    response.headers.get("Authorization").replace("Bearer ", "")
                    if response.headers.get("Authorization") is not None
                    else None
                )

                if response.status > 399:
                    raise SafeRequestError(
                        f"Failed to request {url} with status code {response.status}"
                    )

                return SafeRequestResponseData(
                    data=data,
                    status_code=response.status,
                    cookies=cookies,
                    access_token=access_token,
                )


class SafeRequestEngineRequests(SafeRequestEngine):
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
            method=method.name.lower(),
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
            verify=False,
        )

        if response.status_code > 399:
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


class SafeRequestEngineSelenium(SafeRequestEngine):
    async def request(
        self,
        headers: dict,
        method: SafeRequestMethod,
        url: str,
        data: dict,
        proxy: str,
        timeout: int,
    ) -> SafeRequestResponseData:
        manager = ChromeDriverManager()
        manager_install = await asyncio.to_thread(manager.install)
        options = webdriver.ChromeOptions()

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1420,1080")
        options.add_argument("--headless=new")
        if proxy is not None:
            options.add_argument(f"--proxy-server={proxy}")
        driver = await asyncio.to_thread(
            webdriver.Chrome, service=ChromeService(manager_install), options=options
        )
        driver.get(url)

        all_cookies = driver.get_cookies()
        cookies_dict = {}
        for cookie in all_cookies:
            cookies_dict[cookie["name"]] = cookie["value"]

        return SafeRequestResponseData(
            data=driver.page_source,
            status_code=200,
            cookies=cookies_dict,
            access_token=None,
        )


class SafeRequestEngineUndetectedSelenium(SafeRequestEngine):
    async def request(
        self,
        headers: dict,
        method: SafeRequestMethod,
        url: str,
        data: dict,
        proxy: str,
        timeout: int,
    ) -> SafeRequestResponseData:
        options = uc.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1420,1080")
        options.add_argument("--headless=new")
        if proxy is not None:
            options.add_argument(f"--proxy-server={proxy}")

        driver = await asyncio.to_thread(uc.Chrome, options=options)
        driver.get(url)

        all_cookies = driver.get_cookies()
        cookies_dict = {}
        for cookie in all_cookies:
            cookies_dict[cookie["name"]] = cookie["value"]

        return SafeRequestResponseData(
            data=driver.page_source,
            status_code=200,
            cookies=cookies_dict,
            access_token=None,
        )


class SafeRequestEngineCloudscraper(SafeRequestEngine):
    async def request(
        self,
        headers: dict,
        method: SafeRequestMethod,
        url: str,
        data: dict,
        proxy: str,
        timeout: int,
    ) -> SafeRequestResponseData:
        scraper = await asyncio.to_thread(cloudscraper.create_scraper)
        scraper.ssl_context = ctx
        response = await asyncio.to_thread(
            scraper.request,
            method=method.name.lower(),
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
        )

        if response.status_code > 399:
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


class SafeRequestEngineHttpx(SafeRequestEngine):
    async def request(
        self,
        headers: dict,
        method: SafeRequestMethod,
        url: str,
        data: dict,
        proxy: str,
        timeout: int,
    ) -> SafeRequestResponseData:
        async with httpx.AsyncClient(verify=False, http2=True, proxy=proxy) as client:
            response = await client.request(
                method=method.name.lower(),
                url=url,
                headers=headers,
                json=data,
                timeout=timeout,
                follow_redirects=True,
            )
            if response.status_code > 399:
                raise SafeRequestError(
                    f"Failed to request {url} with status code {response.status_code}"
                )

            return SafeRequestResponseData(
                data=response.text,
                status_code=response.status_code,
                cookies=response.cookies,
                access_token=response.headers.get("Authorization").replace(
                    "Bearer ", ""
                )
                if response.headers.get("Authorization") is not None
                else None,
            )


class SafeRequest:
    def __init__(self, chains: list[SafeRequestEngine] = None):
        self._chains = (
            [
                SafeRequestEngineCloudscraper(),
                SafeRequestEngineHttpx(),
                SafeRequestEngineAiohttp(),
                SafeRequestEngineRequests(),
                SafeRequestEngineSelenium(),
                SafeRequestEngineUndetectedSelenium(),
            ]
            if chains is None
            else chains
        )
        self._headers = {
            "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/json",
            "Connection": "close",
            "Sec-Fetch-Dest": "document",
            "Priority": "u=0, i",
        }
        self._timeout = 30
        self._proxies: list[str] = []
        self._cookies: dict = {}
        self._proxy_opensource = False

    def accept_text_html(self):
        """"""
        self._headers["Accept"] = (
            "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        )

        return self

    def accept_language(self, language: str, is_random: bool = False):
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
                "ja",
                "zh-CN",
                "zh",
            ]
            self._headers["Accept-Language"] = random.choice(languages)
        else:
            self._headers["Accept-Language"] = language

        return self

    async def user_agent(
        self,
        user_agent: Optional[str] = None,
        mobile_random: bool = False,
        pc_random: bool = False,
    ):
        """"""
        if mobile_random:
            ua_engine = await asyncio.to_thread(
                fake_useragent.UserAgent, platforms=["mobile"]
            )
            self._headers["User-Agent"] = ua_engine.random
            self._headers["Sec-Ch-Ua-Platform"] = '"Android"'
            self._headers["Sec-Ch-Ua-Mobile"] = "?0"
            self._headers["Sec-Ch-Ua"] = (
                '"Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"'
            )
        elif pc_random:
            ua_engine = await asyncio.to_thread(
                fake_useragent.UserAgent, platforms=["pc"]
            )
            self._headers["User-Agent"] = ua_engine
        else:
            self._headers["User-Agent"] = user_agent

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

    def cache_control(self, cache_control: str):
        """"""
        self._headers["Cache-Control"] = cache_control

        return self

    def timeout(self, seconds: int):
        """"""
        self._timeout = seconds

        return self

    def header(self, key: str, value: str):
        """"""
        self._headers[key] = value

        return self

    def proxy(self, proxy: str | None = None):
        """"""
        if proxy is None:
            self._proxies = []
        else:
            self._proxies.append(proxy)

        return self

    def proxies(self, proxies: list[str] | str):
        """"""
        if isinstance(proxies, list):
            self._proxies = proxies
        else:
            self._proxies = Lu.map([proxies.split(",")], lambda x: x.strip())

        return self

    def proxy_opensource(self, is_use: bool = False):
        """"""
        self._proxy_opensource = is_use

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
        data: dict = None,
        proxy: str = None,
        timeout: int = 30,
        fn: Optional[
            Callable[[SafeRequestResponseData], SafeRequestResponseData]
        ] = None,
        raise_errors: bool = False,
        max_tries: int = 10,
    ) -> SafeRequestResponseData:
        errors = []
        tries = 0
        return_data = SafeRequestResponseData()

        for chain in self._chains:
            await asyncio.sleep(random.randrange(1, 3))

            if tries >= max_tries:
                return return_data

            proxy = (
                (
                    random.choice(self._proxies + [None])
                    if proxy is None and len(self._proxies) > 0
                    else None
                )
                if not self._proxy_opensource
                else await SafeRequestProxyFacade.get_proxy()
            )

            if self._proxy_opensource:
                if proxy is None:
                    proxy = await SafeRequestProxyFacade.get_proxy()
                else:
                    proxy = (
                        await SafeRequestProxyFacade.get_proxy()
                        if random_bool()
                        else proxy
                    )

                _LOGGER.debug("Using proxy %s", proxy)
            else:
                _LOGGER.debug("Not using proxy")

            try:
                return_data = await chain.request(
                    headers={
                        **self._headers,
                        **{
                            "Host": url.split("/")[2]
                            if url.startswith("http")
                            else url.split("/")[0],
                            "Referer": url,
                            "Origin": url.split("/")[0] + "//" + url.split("/")[2]
                            if url.startswith("http")
                            else url.split("/")[0],
                        },
                        **{
                            "Cookie": "; ".join(
                                [f"{k}={v}" for k, v in self._cookies.items()]
                            ),
                        },
                    },
                    method=method,
                    url=url,
                    data=data,
                    proxy=proxy,
                    timeout=timeout,
                )

                if return_data.status_code <= 399:
                    self.cookie(item=return_data.cookies)

                if fn is not None:
                    return_data = fn(return_data)
                    if return_data is not None and return_data.access_token is not None:
                        self.auth(return_data.access_token)

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
                    f"Failed to request {url} with {chain.__class__.__name__}: {e}"
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
