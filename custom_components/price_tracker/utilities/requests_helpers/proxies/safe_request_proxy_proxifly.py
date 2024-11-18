from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy import (
    SafeRequestProxy,
    RequestProxy,
)


class SafeRequestProxyProxifly(SafeRequestProxy):
    async def fetch(self):
        response = await RequestProxy.request(
            url="https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/all/data.txt",
        )

        data = response.splitlines()

        return data
