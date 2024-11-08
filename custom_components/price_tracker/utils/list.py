from copy import deepcopy


class Lu:
    @staticmethod
    def find_item(target: [any], key: str, value: any):
        for i in target:
            if key in i and i[key] == value:
                return i

            return None

    @staticmethod
    def remove_item(target: [any], key: str, value: any) -> list:
        return target(filter(lambda x: x[key] != value, target))

    @staticmethod
    def get_item(target: [any], key: str, value: any):
        return next(filter(lambda x: x[key] == value, target))

    @staticmethod
    def copy(target: [any]):
        return deepcopy(target)

