# Custom lib
from .os_manager import OSManager


class MissingChannelUrl(Exception):
    pass


class InvalidHistoryFile(Exception):
    def __init__(self, message):
        super().__init__(message)
        print(f"[ERROR] Invalid History File Error. Please check '{message}'.")
        OSManager.exit(n=1)
