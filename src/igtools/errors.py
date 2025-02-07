
class BaseException(Exception):
    pass


class ConfigPathNotExists(BaseException):
    pass


class NoReleaseVersionSetException(BaseException):
    DEFAULT_MESSAGE = "No release version set in configuration"

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


class FinalReleaseException(BaseException):
    DEFAULT_MESSAGE = "The release has been marked as final and cannot be processed further"

    def __init__(self):
        super().__init__(self.DEFAULT_MESSAGE)


class FilePathNotExists(BaseException):
    pass


class FileFormatException(BaseException):
    pass


class DownloadException(BaseException):
    pass


class ExportFormatUnknown(BaseException):
    pass

