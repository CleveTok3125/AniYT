import subprocess
import shlex
import os

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

    def run_mpv_x(
        self,
        url,
        *,
        monitor=1,
        open_app=True,
        mpv_fullscreen_playback=True,
        touch_mouse_gestures=True,
    ):
        mpv_args = self.args.copy()

        os.environ["DISPLAY"] = f":{monitor}"

        if mpv_fullscreen_playback == True:
            mpv_args += ["--fs"]

        mpv_command = ["mpv"] + mpv_args

        if touch_mouse_gestures:
            mpv_command += ["--script=gestures.lua"]

        mpv_command += [url]

        termux_x11_command = ["am", "start", "-n", "com.termux.x11/.MainActivity"]

        if open_app:
            try:
                subprocess.run(termux_x11_command, check=True)
            except FileNotFoundError:
                print("Error: termux-x11 is not installed.")
                OSManager.exit(127)
            except subprocess.CalledProcessError as e:
                print(f"Error running termux-x11: {e}")
                OSManager.exit(e.returncode)

        try:
            subprocess.run(mpv_command, check=True)
        except FileNotFoundError:
            print("Error: mpv is not installed.")
            OSManager.exit(127)
        except subprocess.CalledProcessError as e:
            print(f"Error running mpv_command: {e}")
            OSManager.exit(e.returncode)

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
                f"MPV: \n\n\t{shlex.join(player.command)}\n\nMPV Android: \n\n\t{shlex.join(player.android_command)}\n\n"
            )
            try:
                input("Press Enter to continue...\t")
            except KeyboardInterrupt:
                pass
        elif opts == "termux-x11":
            player.run_mpv_x(url)
        else:
            player.run_mpv()
