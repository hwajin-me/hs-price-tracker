import logging

import pytest

_LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_flow_user_step_no_input(hass):
    _LOGGER.debug(hass)
    """Test appropriate error when no input is provided."""
    _result = await hass.config_entries.flow.async_init(
        "test", context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        _result["flow_id"], user_input={}
    )
    assert {"base": "missing"} == result["errors"]
