from copy import deepcopy


class Lu:
    @staticmethod
    def find_item(target: [any], key: str, value: any):
        return Lu.get_item(target, key, value)

    @staticmethod
    def find_item_by(target: [any], key: str, func):
        return next((x for x in target if func(x[key]) is True), None)

    @staticmethod
    def get(target: [any], key: str, default_value: any = None):
        if key in target:
            return target[key]

        if key.count(".") > 0:
            keys = key.split(".")

            for k in keys:
                if k in target:
                    target = target[k]
                    continue
                else:
                    return default_value
            return target

        return default_value

    @staticmethod
    def update(target: [any], key: str, value: any):
        target[key] = value

        return target

    @staticmethod
    def has(target: [any], key: str):
        if key.count(".") > 0:
            keys = key.split(".")

            for k in keys:
                if k in target:
                    target = target[k]
                else:
                    return False

            return True

        return key in target

    @staticmethod
    def get_or_default(target: [any], key: str, default_value: any = None):
        if key in target:
            return target[key]

        if key.count(".") > 0:
            keys = key.split(".")

            for k in keys:
                if k in target:
                    target = target[k]
                    continue
                else:
                    return default_value
            return target

        return default_value

    @staticmethod
    def remove_item(target: [any], key: str, value: any) -> list:
        return list(filter(lambda x: x[key] != value, target))

    @staticmethod
    def remove(target: [any], fn) -> list:
        return list(filter(fn, target))

    @staticmethod
    def get_item(target: [any], key: str, value: any):
        return next((x for x in target if x[key] == value), None)

    @staticmethod
    def get_item_or_default(
            target: [any], key: str, value: any, default_value: any = None
    ):
        return next((x for x in target if x[key] == value), default_value)

    @staticmethod
    def copy(target: [any]):
        return deepcopy(target)

    @staticmethod
    def map(target: [any], lambda_function):
        return list(map(lambda_function, target))

    @staticmethod
    def filter(target: [any], lambda_function):
        return list(filter(lambda_function, target))
