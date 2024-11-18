from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy import (
    SafeRequestProxy,
    RequestProxy,
)


class SafeRequestProxyProxyscrape(SafeRequestProxy):
    async def fetch(self):
        response = await RequestProxy.request(
            url="https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        )

        return Lu.map(response.split("\r\n"), lambda x: f"http://{x.strip()}")
