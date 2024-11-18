import random
from abc import abstractmethod

import aiohttp


class RequestProxy:
    @staticmethod
    async def request(url: str):
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method="get",
                url=url,
                verify_ssl=False,
            ) as response:
                data = await response.text()

                return data


class SafeRequestProxy:
    def __init__(self, proxies: list[str] = None):
        self._proxies = proxies if proxies else []
        self._request = RequestProxy()

    def random(self):
        return random.choice(self._proxies)

    def all(self):
        return self._proxies

    @abstractmethod
    async def fetch(self) -> list[str]:
        pass
