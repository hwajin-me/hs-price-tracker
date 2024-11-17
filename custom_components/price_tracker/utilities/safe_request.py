import asyncio
import dataclasses
import logging
import random
import ssl
from enum import Enum
from typing import Optional, Callable, Awaitable

import aiohttp
import cloudscraper
import fake_useragent
import httpx
import requests
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from voluptuous import default_factory
from webdriver_manager.chrome import ChromeDriverManager

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
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
    ) -> SafeRequestResponseData:
        pass


class SafeRequestEngineAiohttp(SafeRequestEngine):
    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
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
                    ssl=False,
                    verify_ssl=False,
            ) as response:
                data = await response.text()
                cookies = response.cookies
                access_token = (
                    response.headers.get("Authorization").replace("Bearer ", "")
                    if response.headers.get("Authorization") is not None
                    else None
                )

                if response.status != 200:
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
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
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

        if response.status_code != 200:
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
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
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

        return SafeRequestResponseData(
            data=driver.page_source,
            status_code=200,
            cookies={},
            access_token=None,
        )


class SafeRequestEngineUndetectedSelenium(SafeRequestEngine):
    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
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

        return SafeRequestResponseData(
            data=driver.page_source,
            status_code=200,
            cookies={},
            access_token=None,
        )


class SafeRequestEngineCloudscraper(SafeRequestEngine):
    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
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

        if response.status_code != 200:
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
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
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
            if response.status_code != 200:
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
    _before: Optional[Callable[[], Awaitable[SafeRequestResponseData]]] = None
    _headers: dict
    _timeout: int = 30
    _proxies: list = []
    _cookies = {}
    _chains: list[SafeRequestEngine] = []

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
        }

    def accept_text_html(self):
        """"""
        self._headers["Accept"] = (
            "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        )

        return self

    async def user_agent(self, user_agent: Optional[str] = None, mobile_random: bool = False):
        """"""
        if mobile_random:
            ua_engine = await asyncio.to_thread(fake_useragent.UserAgent, platforms=["mobile"])
            self._headers["User-Agent"] = ua_engine.random
        else:
            self._headers["User-Agent"] = user_agent

        return self

    def user_agent_nexus(self):
        """"""
        self._headers["User-Agent"] = (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
        )

        return self

    def auth(self, token: Optional[str]):
        """"""
        if token is not None:
            self._headers["Authorization"] = f"Bearer {token}"

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
            self._proxies = [proxies.split(",")]

        return self

    def cookie(self, key: str, value: str):
        """"""
        self._cookies[key] = value

        return self

    async def request(
            self,
            url: str,
            method: SafeRequestMethod,
            data: dict = None,
            proxy: str = None,
            timeout: int = 30,
            fn: Optional[
                Callable[[SafeRequestResponseData], SafeRequestResponseData]
            ] = None,
    ) -> SafeRequestResponseData:
        if self._before is not None:
            response = await self._before()
            if fn is not None:
                response = fn(response)

            if response is not None:
                if response.access_token is not None:
                    self.auth(response.access_token)

                if response.cookies is not None:
                    self._cookies.update(response.cookies)

        errors = []

        if proxy is None and len(self._proxies) > 0:
            proxy = random.choice(self._proxies)

        for chain in self._chains:
            await asyncio.sleep(
                random.choice([0.12, 0.23, 0.34, 0.46, 0.58, 0.82, 1.156, 1.234, 1.415, 1.68, 1.894, 2.14021])
            )

            try:
                return await chain.request(
                    headers={
                        **self._headers,
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
            except Exception as e:
                _LOGGER.error(
                    f"Failed to request {url} with {chain.__class__.__name__}: {e}"
                )
                errors.append(e)
                pass

        if len(errors) > 0:
            raise errors[0]

        raise SafeRequestError("No request engine found")
