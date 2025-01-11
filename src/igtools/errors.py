
class BaseException(Exception):
    pass


class ConfigPathNotExists(BaseException):
    pass


class NoVersionSetException(BaseException):
    DEFAULT_MESSAGE = "No version set in configuration"

    def __init__(self):
        super().__init__(self.DEFAULT_MESSAGE)


class ReleaseAlreadyExistsException(BaseException):
    pass


class ReleaseNotFoundException(BaseException):
    pass


class DuplicateRequirementIDException(BaseException):
    pass


class ReleaseNotesOutputPathNotExists(BaseException):
    pass


