from time import sleep

from .helper import IOHelper
from .os_manager import OSManager


class MissingChannelUrl(Exception):
    pass


class InvalidHistoryFile(Exception):
    def __init__(self, message):
        super().__init__(message)
        print(f"[ERROR] Invalid History File Error. Please check '{message}'.")
        print(
            f"You can delete {message} and let the program recreate it when viewing a new video."
        )
        OSManager.exit(n=1)


class PauseableException(Exception):
    @IOHelper.gracefully_terminate
    def __init__(self, message, delay=3):
        super().__init__(message)
        if delay < 0:
            input(f"{message}\n")
        else:
            print(message)
            sleep(delay)
