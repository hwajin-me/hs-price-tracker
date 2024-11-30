import asyncio
import dataclasses
import json
import logging
import random
import ssl
from enum import Enum
from typing import Optional, Callable, Self, Awaitable

import aiohttp
import cloudscraper
import fake_useragent
import httpx
import requests
import undetected_chromedriver as uc
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.client_config import ClientConfig
from selenium.webdriver.remote.command import Command
from voluptuous import default_factory
from webdriver_manager.chrome import ChromeDriverManager

from custom_components.price_tracker.utilities.list import Lu


def bot_agents():
    return ["NaverBot", "Yeti", "Googlebot-Mobile", "HTTPie/3.2.4"]


def ssl_context():
    ctx = ssl.SSLContext()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    return ctx


_LOGGER = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
        return self.status_code is not None and self.status_code <= 399 and self.data is not None and self.data != ""

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
            session: Optional[requests.Session] = None,
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
            session: Optional[requests.Session] = None,
    ) -> SafeRequestResponseData:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                    method=method.name.lower(),
                    url=url,
                    headers=headers,
                    json=data,
                    data=data,
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
            session: Optional[requests.Session] = None,
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


class SafeRequestEngineSelenium(SafeRequestEngine):
    def __init__(self, remote: str = None, proxies: list[str] = None):
        self._remote = (
            remote if remote is not None and str(remote).strip() != "" else None
        )
        self._proxies = proxies if proxies is not None else []

    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict,
            proxy: str,
            timeout: int,
            session: Optional[requests.Session] = None,
    ) -> SafeRequestResponseData:
        driver = None
        try:
            options = await asyncio.to_thread(webdriver.ChromeOptions)

            options.add_argument("--lang=en")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-session-crashed-bubble")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("detach", True)
            options.add_experimental_option("useAutomationExtension", False)
            if headers.get("User-Agent") is not None:
                options.add_argument(f"--user-agent={headers.get('User-Agent')}")
            options.page_load_strategy = "eager"

            if proxy is not None:
                _LOGGER.debug("Using proxy for selenium %s", proxy)
                options.add_argument(f"--proxy-server={proxy}")

            if self._proxies and len(self._proxies) > 0:
                _LOGGER.debug("Using random proxy for selenium in %s", self._proxies)
                options.add_argument(f"--proxy-server={random.choice(self._proxies)}")

            if self._remote is None:
                manager = await asyncio.to_thread(ChromeDriverManager)
                manager_install = await asyncio.to_thread(manager.install)
                service = await asyncio.to_thread(
                    Service, executable_path=manager_install
                )
                driver = await asyncio.to_thread(
                    webdriver.Chrome, service=service, options=options
                )
            else:
                driver = await asyncio.to_thread(
                    webdriver.Remote,
                    command_executor=self._remote,
                    options=options,
                    client_config=ClientConfig(
                        remote_server_addr=self._remote,
                        keep_alive=False,
                        timeout=timeout,
                        ignore_certificates=True,
                    ),
                )

            await asyncio.to_thread(driver.implicitly_wait, time_to_wait=timeout)
            await asyncio.to_thread(driver.set_page_load_timeout, time_to_wait=timeout)
            await asyncio.to_thread(
                driver.execute_script,
                script="Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            )
            await asyncio.to_thread(driver.get, url=url)

            all_cookies = await asyncio.to_thread(driver.get_cookies)
            cookies_dict = {}
            for cookie in all_cookies:
                cookies_dict[cookie["name"]] = cookie["value"]
            page_source = (
                await asyncio.to_thread(
                    driver.execute, driver_command=Command.GET_PAGE_SOURCE
                )
            )["value"]

            data = SafeRequestResponseData(
                data=page_source,
                status_code=200,
                cookies=cookies_dict,
                access_token=None,
            )

        finally:
            if driver is not None:
                await asyncio.to_thread(driver.quit)

        return data


class SafeRequestEngineUndetectedSelenium(SafeRequestEngine):
    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict,
            proxy: str,
            timeout: int,
            session: Optional[requests.Session] = None,
    ) -> SafeRequestResponseData:
        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1420,1080")
            options.add_argument("--headless=new")
            if proxy is not None:
                options.add_argument(f"--proxy-server={proxy}")

            driver = await asyncio.to_thread(uc.Chrome, options=options, headless=True)

            await asyncio.to_thread(driver.implicitly_wait, time_to_wait=timeout)
            await asyncio.to_thread(driver.set_page_load_timeout, time_to_wait=timeout)

            # TODO: Add Post Request
            driver.get(url)

            all_cookies = await asyncio.to_thread(driver.get_cookies)
            cookies_dict = {}
            for cookie in all_cookies:
                cookies_dict[cookie["name"]] = cookie["value"]

            data = SafeRequestResponseData(
                data=await asyncio.to_thread(driver.page_source),
                status_code=200,
                cookies=cookies_dict,
                access_token=None,
            )
        finally:
            if driver is not None:
                await asyncio.to_thread(driver.quit)

        return data


class SafeRequestEngineCloudscraper(SafeRequestEngine):
    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: any,
            proxy: str,
            timeout: int,
            session: Optional[requests.Session] = None,
    ) -> SafeRequestResponseData:
        scraper = await asyncio.to_thread(
            cloudscraper.create_scraper,
            browser="chrome",
            delay=1,
            ssl_context=ssl_context(),
            sess=session,
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
            verify=False,
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


class SafeRequestEngineHttpx(SafeRequestEngine):
    async def request(
            self,
            headers: dict,
            method: SafeRequestMethod,
            url: str,
            data: dict,
            proxy: str,
            timeout: int,
            session: Optional[requests.Session] = None,
    ) -> SafeRequestResponseData:
        async with httpx.AsyncClient(verify=False, proxy=proxy) as client:
            response = await client.request(
                method=method.name.lower(),
                url=url,
                headers=headers,
                json=data,
                timeout=timeout,
                follow_redirects=True,
            )
            if response.status_code > 399 and response.status_code != 404:
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
    def __init__(
            self,
            chains: list[SafeRequestEngine] = None,
            proxies: list[str] = None,
            cookies: dict = None,
            headers: dict = None,
            selenium: Optional[str] = None,
            selenium_proxy: Optional[list[str]] = None,
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
        self._session = None

        if self._selenium is not None and str(selenium).strip() != "":
            self._chains.append(
                SafeRequestEngineSelenium(
                    remote=self._selenium, proxies=self._selenium_proxy
                )
            )
        self._chains = self._chains + (
            [
                SafeRequestEngineCloudscraper(),
                SafeRequestEngineAiohttp(),
                SafeRequestEngineRequests(),
                SafeRequestEngineHttpx(),
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
                "ja",
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
                'Host': url.split('/')[2] if 'Host' not in self._headers else self._headers['Host'],
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
                    session=self._session,
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
