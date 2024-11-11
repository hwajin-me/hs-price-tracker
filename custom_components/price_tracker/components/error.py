class UnsupportedError(Exception):
    pass


class InvalidError(Exception):
    pass


class ApiError(Exception):
    pass


class NotFoundError(Exception):
    pass


class DataFetchError(Exception):
    pass


class DataFetchErrorCauseEmpty(DataFetchError):
    pass
