import os
import shlex
import subprocess

from .os_manager import OSManager


class Termux_X11_OPTS:
    monitor: int = 1
    open_app: bool = True
    return_app: bool = True
    mpv_fullscreen_playback: bool = True
    touch_mouse_gestures: bool = True


class Player:
    def __init__(self, url, args=None):
        mpv_config_path = "./mpv-config/custom.conf"
        custom_config_exists = OSManager.exists(mpv_config_path)
        if args is None and custom_config_exists:
            self.args = [f"--input-conf={mpv_config_path}"]
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

    def app_subprocess_helper(self, app_name, commands):
        try:
            subprocess.run(commands, check=True)
        except FileNotFoundError:
            print(f"Error: {app_name} is not installed.")
            OSManager.exit(127)
        except subprocess.CalledProcessError as e:
            print(f"Error running {app_name}: {e}")
            OSManager.exit(e.returncode)

    def run_mpv_x(
        self,
        url,
        *,
        monitor=None,
        open_app=None,
        return_app=None,
        mpv_fullscreen_playback=None,
        touch_mouse_gestures=None,
    ):
        defaults = Termux_X11_OPTS
        params = {
            "monitor": monitor,
            "open_app": open_app,
            "return_app": return_app,
            "mpv_fullscreen_playback": mpv_fullscreen_playback,
            "touch_mouse_gestures": touch_mouse_gestures,
        }

        for key, value in params.items():
            if value is None:
                params[key] = getattr(defaults, key)

        mpv_args = self.args.copy()

        os.environ["DISPLAY"] = f":{monitor}"

        if mpv_fullscreen_playback is True:
            mpv_args += ["--fs"]

        mpv_command = ["mpv"] + mpv_args

        if touch_mouse_gestures:
            mpv_command += [
                "--no-window-dragging",
                "--script=./mpv-scripts/gestures.lua",
                "--script=./mpv-scripts/sponsorblock_minimal.lua",
            ]

        mpv_command += [url]

        termux_x11_command = ["am", "start", "-n", "com.termux.x11/.MainActivity"]

        termux_command = [
            "am",
            "start",
            "-n",
            "com.termux/com.termux.app.TermuxActivity",
        ]

        if open_app:
            self.app_subprocess_helper("termux-x11", termux_x11_command)

        self.app_subprocess_helper("mpv", mpv_command)

        if return_app:
            self.app_subprocess_helper("termux", termux_command)

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
