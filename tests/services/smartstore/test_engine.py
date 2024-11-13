import pytest
from pytest_socket import enable_socket, socket_allow_hosts

from custom_components.price_tracker.services.smartstore.engine import SmartstoreEngine


@pytest.mark.enable_socket
@pytest.hookimpl(trylast=True)
@pytest.mark.asyncio
async def test_naver_smartstore_parse_1():
    enable_socket()
    socket_allow_hosts(
        allow_unix_socket=True,
    )
    engine = SmartstoreEngine(
        item_url="https://m.smartstore.naver.com/thereco-store/products/10147611205"
    )
    result = await engine.load()

    assert result is not None
    assert result.name is not None
