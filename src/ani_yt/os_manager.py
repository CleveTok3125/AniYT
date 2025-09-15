import os
import sys
from tempfile import mkdtemp

from .extension import Extension


class OSManager:
    @Extension.check_module_update
    @staticmethod
    def exit(n=0):
        sys.exit(n)

    @staticmethod
    def exists(path):
        if os.path.exists(path):
            return True
        return False

    @staticmethod
    def isdir(directory):
        if os.path.isdir(directory):
            return True
        return False

    @staticmethod
    def delete_file(path):
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(e)

    @staticmethod
    def android_check():
        return (
            True
            if os.name == "posix"
            and (
                "android" in os.uname().release.lower()
                or "com.termux" in os.environ.get("PREFIX", "")
            )
            else False
        )

    @staticmethod
    def temporary_session():
        temp_path = mkdtemp(prefix="AniYT_")
        os.chdir(temp_path)
        return temp_path

    @staticmethod
    def working_directory(directory):
        abs_path = os.path.abspath(os.path.normpath(directory))
        if not OSManager.isdir(abs_path):
            return None, None
        os.chdir(abs_path)
        return directory, abs_path

    @staticmethod
    def initialize_directory(dirs):
        for dir in dirs:
            os.makedirs(dir, exist_ok=True)
