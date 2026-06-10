from ..errors import BaseException


class MigrationError(BaseException):
    pass


class MigrationRuntimeError(BaseException):
    pass