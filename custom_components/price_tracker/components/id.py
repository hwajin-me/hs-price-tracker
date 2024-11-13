from custom_components.price_tracker.consts.defaults import DOMAIN


class IdGenerator:
    @staticmethod
    def generate_entity_id(
        service_type: str, entity_target: str, device_id: str | None = None
    ) -> str:
        if device_id is None or device_id == "":
            return DOMAIN + ".price_{}_type_{}".format(service_type, entity_target)

        return DOMAIN + ".price_{}_type_{}_device_{}".format(
            service_type, device_id, entity_target
        )

    @staticmethod
    def generate_device_id(device_target: str) -> str:
        return DOMAIN + ".price-device_{}".format(device_target)

    @staticmethod
    def get_entity_target_from_id(entity_id: str) -> str:
        target = entity_id.removeprefix(DOMAIN + ".price_").split("_type_")[1]

        if "_device_" in target:
            return target.split("_device_")[1]

        return target

    @staticmethod
    def get_entity_device_target_from_id(entity_id: str) -> str:
        target = entity_id.removeprefix(DOMAIN + ".price_").split("_type_")[1]

        if "_device_" in target:
            return target.split("_device_")[0]

        return target

    @staticmethod
    def get_device_target_from_id(device_id: str) -> str:
        return device_id.removeprefix(DOMAIN + ".price-device_")

    @staticmethod
    def is_device_id(entity_id: str) -> bool:
        return entity_id.startswith(DOMAIN + ".price-device_")
