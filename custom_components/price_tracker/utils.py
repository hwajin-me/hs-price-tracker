import hashlib

import aiohttp

from custom_components.price_tracker.components.error import ApiError
from custom_components.price_tracker.const import REQUEST_DEFAULT_HEADERS


def find_item(list: [dict], key: str, value: any):
    for i in list:
        if key in i and i[key] == value:
            return i

    return None


async def request(method: str, url: str, headers=None):
    if headers is None:
        headers = {}

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        async with session.request(method=method, url=url, headers={**REQUEST_DEFAULT_HEADERS, **headers}) as response:
            if response.status > 299:
                raise ApiError(
                    "Error while fetching data from the API (status code: {}, {}, {}, {})".format(response.status, url,
                                                                                                  headers,
                                                                                                  await response.text()))

            return await response.read()


async def request_plain(url: str, headers=None):
    if headers is None:
        headers = {}

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        async with session.get(url=url, headers={**REQUEST_DEFAULT_HEADERS, **headers}) as response:
            return response


def findValueOrDefault(list: [dict], key: str, defaultValue: any = None):
    return list[key] if key in list and list[key] is not None else defaultValue


def removeItem(list: [any], key: str, value: any):
    return list(filter(lambda x: x[key] != value, list))


def parseNumber(value: any):
    return float(str(value).replace(",", "").replace(" ", ""))


def sha256(value: str):
    target = hashlib.sha256()
    target.update(value.encode('utf-8'))
    return target.hexdigest()


def md5(value: str):
    target = hashlib.md5()
    target.update(value.encode('utf-8'))
    return target.hexdigest()
