import subprocess

import requests

from .helper import SubprocessHelper


class Extension:
    check_update_enabled = True

    class CheckModuleUpdate:
        @staticmethod
        def check_yt_dlp(name="yt-dlp"):
            print("\n[Extension] Checking for yt-dlp update...")

            SubprocessHelper.app_subprocess_help("yt-dlp", check_only=True)

            old_ver = (
                subprocess.check_output(["yt-dlp", "--version"]).decode("utf-8").strip()
            )
            old_ver = ".".join(str(int(part)) for part in old_ver.split("."))

            try:
                new_ver = requests.get(
                    "https://pypi.org/pypi/yt-dlp/json", timeout=10
                ).json()["info"]["version"]
            except requests.exceptions.Timeout:
                new_ver = old_ver
                print("Update check request timed out.")
            return (old_ver == new_ver, name, old_ver, new_ver)

        @staticmethod
        def print_notice(update_info):
            if not update_info[0]:
                print(
                    f"\n\033[34m[notice]\033[0m A new release of {update_info[1]} is available: \033[31m{update_info[2]}\033[0m -> \033[32m{update_info[3]}\033[0m"
                )
                print(
                    f"\033[34m[notice]\033[0m To update, run: \033[32mpython -m pip install --upgrade {update_info[1]}\033[0m"
                )

    @staticmethod
    def check_module_update(func):
        def wrapper(*args, **kwargs):
            check_update = Extension.check_update_enabled

            if check_update:
                yt_dlp_update_info = Extension.CheckModuleUpdate.check_yt_dlp()
                Extension.CheckModuleUpdate.print_notice(yt_dlp_update_info)

            return func(*args, **kwargs)

        return wrapper
