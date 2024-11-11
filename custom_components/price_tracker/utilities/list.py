from copy import deepcopy


class Lu:
    @staticmethod
    def find_item(target: [any], key: str, value: any):
        for i in target:
            if key in i and i[key] == value:
                return i

            return None

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
        return next(filter(lambda x: x[key] == value, target))

    @staticmethod
    def copy(target: [any]):
        return deepcopy(target)

    @staticmethod
    def map(target: [any], lambda_function):
        return list(map(lambda_function, target))
