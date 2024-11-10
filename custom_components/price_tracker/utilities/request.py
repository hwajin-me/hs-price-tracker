import asyncio
import random

import aiohttp
import requests

from custom_components.price_tracker.components.error import ApiError

_REQUEST_DEFAULT_HEADERS = {
    'Accept': 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Connection': 'close',
    'Cache-Control': 'max-age=0',
}


def proxy_server()-> str:
    return random.choice([
        'http://8.220.204.215:9098',
        'http://3.37.125.76:3128',
        'http://43.201.121.81:80',
        'http://138.2.116.87:65530',
        'http://211.206.45.9:44410',
        'http://118.218.126.54:9400',
        'http://211.194.214.128:9050',
        'http://8.213.137.155:1720',
        'http://115.22.22.109:80',
        'http://8.220.204.92:80',
        'http://121.124.124.147:3128'
    ])


def default_request_headers():
    return _REQUEST_DEFAULT_HEADERS


async def http_request(method: str, url: str, headers=None, auth: str = None, timeout: int = 10, proxy: bool = False):
    if headers is None:
        headers = {}

    if auth is not None:
        headers['Authorization'] = 'Bearer {}'.format(auth)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        try:
            async with session.request(method=method, url=url, headers={**_REQUEST_DEFAULT_HEADERS, **headers},
                                       timeout=timeout, proxy=proxy_server() if proxy else None) as response:
                if response.status > 299:
                    raise ApiError(
                        "Error while fetching data from the API (status code: {}, {}, {}, {})".format(response.status,
                                                                                                      url,
                                                                                                      headers,
                                                                                                      await response.text()))

                return response

        except asyncio.TimeoutError as e:
            if proxy:
                return await http_request(method, url, headers, auth, timeout, False)
            else:
                raise ApiError(
                    "Timeout while fetching data from the API (url: {}, headers: {})".format(url, headers)) from e


async def http_request_async(method: str, url: str, headers=None, auth: str = None, timeout: int = 10, proxy: bool = False):
    if headers is None:
        headers = {}

    if auth is not None:
        headers['Authorization'] = 'Bearer {}'.format(auth)

    req = requests.get if method == 'get' else requests.post
    response = await asyncio.to_thread(req, url,
                                       headers={**_REQUEST_DEFAULT_HEADERS, **headers})
    if response is not None:
        if response.status_code > 299:
            raise ApiError(
                "Error while fetching data from the API (status code: {}, {}, {}, {})".format(response.status_code,
                                                                                              url,
                                                                                              headers,
                                                                                              response.text))

        return response