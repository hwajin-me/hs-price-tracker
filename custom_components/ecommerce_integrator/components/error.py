class UnsupportedError(Exception):
    pass


class InvalidError(Exception):
    pass


class ApiError(Exception):
    pass


class ApiAuthError(ApiError):
    pass


class NotFoundError(Exception):
    pass


class DataFetchError(Exception):
    pass


class DataFetchErrorCauseEmpty(DataFetchError):
    pass


class DataParseError(Exception):
    pass


class InvalidItemUrlError(InvalidError):
    pass
