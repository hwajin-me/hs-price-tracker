from custom_components.price_tracker.utilities.list import Lu
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy import (
    SafeRequestProxy,
    RequestProxy,
)


class SafeRequestProxyKang(SafeRequestProxy):
    async def fetch(self):
        response_http = await RequestProxy.request(
            url="https://raw.githubusercontent.com/officialputuid/KangProxy/refs/heads/KangProxy/http/http.txt",
        )

        http = Lu.map(response_http.split("\r\n"), lambda x: f"http://{x.strip()}")

        response_https = await RequestProxy.request(
            url="https://raw.githubusercontent.com/officialputuid/KangProxy/refs/heads/KangProxy/https/https.txt",
        )

        https = Lu.map(response_https.split("\r\n"), lambda x: f"https://{x.strip()}")

        response_sock5 = await RequestProxy.request(
            url="https://raw.githubusercontent.com/officialputuid/KangProxy/refs/heads/KangProxy/socks5/socks5.txt",
        )

        sock5 = Lu.map(response_sock5.split("\r\n"), lambda x: f"socks5://{x.strip()}")

        # Filtering non ip:port
        http = Lu.filter(http, lambda x: len(x.split(":")) == 2)
        https = Lu.filter(https, lambda x: len(x.split(":")) == 2)
        sock5 = Lu.filter(sock5, lambda x: len(x.split(":")) == 2)

        # Filtering 0.0.0.0
        http = Lu.filter(http, lambda x: not x.startswith("http://0.0.0.0"))
        https = Lu.filter(https, lambda x: not x.startswith("https://0.0.0.0"))
        sock5 = Lu.filter(sock5, lambda x: not x.startswith("socks5://0.0.0.0"))

        return http + https + sock5
