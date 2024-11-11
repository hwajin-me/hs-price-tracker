from copy import deepcopy


class Lu:
    @staticmethod
    def find_item(target: [any], key: str, value: any):
        return Lu.get_item(target, key, value)

    @staticmethod
    def get(target: [any], key: str):
        if key in target:
            return target[key]

        return None

    @staticmethod
    def get_or_default(target: [any], key: str, default_value: any = None):
        if key in target:
            return target[key]

        return default_value

    @staticmethod
    def remove_item(target: [any], key: str, value: any) -> list:
        return target(filter(lambda x: x[key] != value, target))

    @staticmethod
    def get_item(target: [any], key: str, value: any):
        return next((x for x in target if x[key] == value), None)

    @staticmethod
    def copy(target: [any]):
        return deepcopy(target)

    @staticmethod
    def map(target: [any], lambda_function):
        return list(map(lambda_function, target))
