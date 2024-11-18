from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy import (
    SafeRequestProxy,
    RequestProxy,
)


class SafeRequestProxyVakhov(SafeRequestProxy):
    async def fetch(self):
        response_http = await RequestProxy.request(
            url="https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/http.txt",
        )

        http = Lu.map(response_http.split("\r\n"), lambda x: f"http://{x.strip()}")

        response_sock5 = await RequestProxy.request(
            url="https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/socks5.txt",
        )

        sock5 = Lu.map(response_sock5.split("\r\n"), lambda x: f"socks5://{x.strip()}")

        # Filtering non ip:port
        http = Lu.filter(http, lambda x: len(x.split(":")) == 2)
        sock5 = Lu.filter(sock5, lambda x: len(x.split(":")) == 2)

        return http + sock5
