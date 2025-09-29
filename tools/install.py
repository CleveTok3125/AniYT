#!/usr/bin/env python3
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import urllib.request


class Installer:
    API_URL = "https://api.github.com/repos/CleveTok3125/AniYT/releases/latest"
    PYTHON_TAG = None
    PLATFORM_TAG = None
    ARCH = None
    WHL_URL = None
    HASH_URL = None

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
    def get_sys_info():
        Installer.PYTHON_TAG = f"cp{sys.version_info[0]}{sys.version_info[1]}"
        Installer.ARCH = platform.machine()  # aarch64, x86_64, arm64

        if Installer.android_check():
            Installer.PLATFORM_TAG = f"android_{Installer.ARCH}"
        elif platform.system().lower() == "linux":
            Installer.PLATFORM_TAG = f"linux_{Installer.ARCH}"
        elif platform.system().lower() == "darwin":
            Installer.PLATFORM_TAG = f"macosx_12_0_{Installer.ARCH}"
        elif platform.system().lower() == "windows":
            arch_map = {"AMD64": "amd64", "ARM64": "arm64"}
            Installer.PLATFORM_TAG = (
                f"win_{arch_map.get(Installer.ARCH, Installer.ARCH)}"
            )
        else:
            Installer.PLATFORM_TAG = f"{platform.system().lower()}_{Installer.ARCH}"

    @staticmethod
    def find_wheel():
        with urllib.request.urlopen(Installer.API_URL) as resp:
            data = json.load(resp)

        for asset in data.get("assets", []):
            url = asset.get("browser_download_url", "")
            if (
                url.endswith(".whl")
                and Installer.PYTHON_TAG in url
                and Installer.PLATFORM_TAG in url
                and Installer.ARCH in url
            ):
                Installer.WHL_URL = url
                Installer.HASH_URL = url + ".sha256"
                break

        if not Installer.WHL_URL:
            print(
                f"Error: No wheel found for Python {Installer.PYTHON_TAG} and platform {Installer.PLATFORM_TAG}"
            )
            sys.exit(1)

    @staticmethod
    def verify_hash(local_file):
        if not Installer.HASH_URL:
            print("No hash provided, skipping verification.")
            return

        with urllib.request.urlopen(Installer.HASH_URL) as resp:
            expected_hash = resp.read().decode().strip().split()[0]

        sha256 = hashlib.sha256()
        with open(local_file, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()

        if actual_hash.lower() != expected_hash.lower():
            print(
                f"Error: SHA256 mismatch!\nExpected: {expected_hash}\nActual:   {actual_hash}"
            )
            sys.exit(1)
        print("SHA256 hash verified.")

    @staticmethod
    def install_wheel():
        print(f"Installing wheel: {Installer.WHL_URL}")
        download_dir = tempfile.gettempdir()
        filename = os.path.basename(Installer.WHL_URL)
        local_file = os.path.join(download_dir, filename)
        urllib.request.urlretrieve(Installer.WHL_URL, local_file)
        Installer.verify_hash(local_file)

        if Installer.android_check():
            new_file = local_file.replace("android", "linux")
            os.rename(local_file, new_file)
            local_file = new_file

        subprocess.check_call([sys.executable, "-m", "pip", "install", local_file])

    @staticmethod
    def start():
        Installer.get_sys_info()
        Installer.find_wheel()
        Installer.install_wheel()


if __name__ == "__main__":
    Installer.start()
