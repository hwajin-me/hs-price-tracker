import asyncio
import random
from typing import Unpack

import aiohttp
import requests
from aiohttp.client import _RequestOptions
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from custom_components.price_tracker.components.error import ApiError, ApiAuthError

_REQUEST_DEFAULT_HEADERS = {
    "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Cache-Control": "max-age=0",
    "Content-Type": "application/json",
    "Connection": "close",
}


def mobile_ua() -> str:
    return UserAgent(platforms=["mobile"], os="android").random


def proxy_server() -> str:
    return random.choice(
        [
            "http://8.220.204.215:9098",
            "http://3.37.125.76:3128",
            "http://43.201.121.81:80",
            "http://138.2.116.87:65530",
            "http://211.206.45.9:44410",
            "http://118.218.126.54:9400",
            "http://211.194.214.128:9050",
            "http://8.213.137.155:1720",
            "http://115.22.22.109:80",
            "http://8.220.204.92:80",
            "http://121.124.124.147:3128",
        ]
    )


def default_request_headers():
    return _REQUEST_DEFAULT_HEADERS


async def http_request(
    method: str,
    url: str,
    headers=None,
    auth: str = None,
    timeout: int | None = 5,
    json: dict = None,
    proxy: bool = False,
    is_retry: bool = False,
    skip_auto_headers: list[str] = None,
    **kwargs: Unpack[_RequestOptions],
):
    if headers is None:
        headers = {}

    if auth is not None:
        headers["authorization"] = "Bearer {}".format(auth)

    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(
            verify_ssl=False, use_dns_cache=False, limit=10240
        )
    )

    try:
        response = await session.request(
            method=method,
            url=url,
            headers={
                **{k.lower(): v for k, v in _REQUEST_DEFAULT_HEADERS.items()},
                **{k.lower(): v for k, v in headers.items()},
            },
            timeout=timeout,
            json=json,
            allow_redirects=True,
            max_redirects=99,
            proxy=proxy_server() if proxy else None,
            skip_auto_headers=skip_auto_headers
            if skip_auto_headers
            else ["User-Agent", "Content-Type", "Accept", "Content-Length"],
            **kwargs,
        )
        if response.status == 401 or response.status == 403:
            raise ApiAuthError(
                "API authentication error {} {}".format(
                    response.request_info.headers, response.text
                )
            )

        data = {"status_code": response.status, "data": await response.text()}
        await session.close()

        return data
    except aiohttp.ServerConnectionError as e:
        raise ApiError(
            "Error while fetching data from the API - ServerConnectionError (url: {}, headers: {}) {}".format(
                url, headers, e
            )
        ) from e
    except aiohttp.ClientConnectionError as e:
        if is_retry:
            raise ApiError(
                "Error while fetching data from the API - ClientConnectionError (url: {}, headers: {}) {}".format(
                    url, headers, e
                )
            ) from e
        else:
            return await http_request(
                method, url, headers, auth, timeout, json, proxy, True
            )
    except asyncio.TimeoutError as e:
        if proxy:
            return await http_request(method, url, headers, auth, timeout, json, False)
        else:
            raise ApiError(
                "Timeout while fetching data from the API (url: {}, headers: {})".format(
                    url, headers
                )
            ) from e
    finally:
        await session.close()


class ResponseData:
    text: str
    status_code: int

    def __init__(self, data: str, status_code: int):
        self.text = data
        self.status_code = status_code


async def http_request_selenium(url: str):
    manager = ChromeDriverManager()
    manager_install = await asyncio.to_thread(manager.install)
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1420,1080")
    options.add_argument("--headless=new")
    driver = await asyncio.to_thread(
        webdriver.Chrome, service=ChromeService(manager_install), options=options
    )
    driver.get(url)

    return driver.page_source


async def http_request_async(
    method: str,
    url: str,
    headers=None,
    auth: str = None,
    timeout: int = 5,
    proxy: bool = False,
    **kwargs: Unpack[_RequestOptions],
):
    if headers is None:
        headers = {}

    if auth is not None and auth != "":
        headers["authorization"] = "Bearer {}".format(auth)

    req = requests.get if method == "get" else requests.post
    try:
        response = await asyncio.to_thread(
            req,
            url,
            headers={
                **{k.lower(): v for k, v in _REQUEST_DEFAULT_HEADERS.items()},
                **{k.lower(): v for k, v in _REQUEST_DEFAULT_HEADERS.items()},
                **{k.lower(): v for k, v in headers.items()},
            },
            timeout=timeout,
            verify=False,
        )
    except Exception:
        data = await http_request(
            method, url, headers, auth, timeout, proxy=proxy, **kwargs
        )

        return ResponseData(data["data"], data["status_code"])
    if response is not None:
        if response.status_code > 399:
            data = await http_request(
                method, url, headers, auth, timeout, proxy=proxy, **kwargs
            )

            return ResponseData(data["data"], data["status_code"])

        return response
    else:
        data = await http_request(
            method, url, headers, auth, timeout, proxy=proxy, **kwargs
        )

        return ResponseData(data["data"], data["status_code"])
