from custom_components.price_tracker.consts.defaults import DOMAIN

ENTITY_ID_FORMAT = DOMAIN + ".price_{}_{}"
DEVICE_ENTITY_ID_FORMAT = DOMAIN + ".price_device_{}"


def entity_id_format(device_id: str, product_id: str) -> str:
    return ENTITY_ID_FORMAT.format(device_id, product_id)


def device_entity_id_format(device_id: str) -> str:
    return DEVICE_ENTITY_ID_FORMAT.format(device_id)
