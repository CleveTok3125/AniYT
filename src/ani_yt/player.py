import subprocess

# Custom lib
from .os_manager import OSManager


class Player:
    def __init__(self, url, args=None):
        custom_config_exists = OSManager.exists("custom.conf")
        if args is None and custom_config_exists:
            self.args = ["--input-conf=custom.conf"]
        elif args is None and not custom_config_exists:
            self.args = []
        else:
            self.args = args
        self.command = ["mpv"] + self.args + [url]

        self.android_command = [
            "am",
            "start",
            "-a",
            "android.intent.action.VIEW",
            "-t",
            "video/any",
            "-p",
            "is.xyz.mpv.ytdl",
            "-d",
            url,
        ]

    def run_mpv(self):  # optional: use sponsorblock for mpv to automatically skip op/en
        try:
            subprocess.run(self.command)
        except FileNotFoundError:
            print("Error running command: MPV is not installed.")
            OSManager.exit(127)

    def run_mpv_android(
        self,
    ):  # require https://github.com/mpv-android/mpv-android/pull/58
        try:
            subprocess.run(self.android_command)
        except FileNotFoundError:
            print("Error running command: Current OS may not be Android.")
            OSManager.exit(127)

    def start(self):
        if OSManager.android_check():
            self.run_mpv_android()
        else:
            self.run_mpv()

    @staticmethod
    def start_with_mode(url, opts="auto"):
        print("Playing...")

        player = Player(url)

        if opts == "auto":
            player.start()
        elif opts == "android":
            player.run_mpv_android()
        elif opts == "ssh":
            print("Copy one of the commands below:")
            print(
                f"MPV: \n\n\t{' '.join(player.command)}\n\nMPV Android: \n\n\t{' '.join(player.android_command)}\n\n"
            )
            try:
                input("Press Enter to continue...\t")
            except KeyboardInterrupt:
                pass
        else:
            player.run_mpv()
