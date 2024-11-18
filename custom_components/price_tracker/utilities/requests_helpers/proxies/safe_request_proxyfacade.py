import logging
import random
from datetime import datetime, timedelta

from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy import (
    SafeRequestProxy,
)
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy_ercindedeoglu import (
    SafeRequestProxyErcindedeoglu,
)
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy_kang import (
    SafeRequestProxyKang,
)
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy_mmpx12 import (
    SafeRequestProxyMmpx12,
)
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy_proxifly import (
    SafeRequestProxyProxifly,
)
from custom_components.price_tracker.utilities.requests_helpers.proxies.safe_request_proxy_proxyscrape import (
    SafeRequestProxyProxyscrape,
)

_LOGGER = logging.getLogger(__name__)


class SafeRequestProxyFacade:
    _proxy_engines: list[SafeRequestProxy] = [
        SafeRequestProxyProxyscrape(),
        SafeRequestProxyErcindedeoglu(),
        SafeRequestProxyKang(),
        SafeRequestProxyMmpx12(),
        SafeRequestProxyProxifly(),
    ]
    _proxies: list[str] = []
    _updated_at: datetime | None = None

    @classmethod
    async def get_proxy(cls) -> str:
        if cls._updated_at is None or (
            datetime.now() - cls._updated_at
        ).min > timedelta(minutes=60):
            cls._updated_at = datetime.now()
            for proxy in cls._proxy_engines:
                try:
                    data = await proxy.fetch()
                    if data:
                        cls._proxies = list(set().union(cls._proxies, data))
                except Exception as e:
                    _LOGGER.error(
                        f"Failed to fetch proxies from {proxy.__class__.__name__}: {e}"
                    )

        return random.choice(cls._proxies)
