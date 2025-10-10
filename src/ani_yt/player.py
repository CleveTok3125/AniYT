import os
import shlex

from .helper import SubprocessHelper
from .input_handler import InputHandler
from .os_manager import OSManager


class PlayerConfig:
    _settings = {
        "mpv_args": [
            "--save-position-on-quit=yes",
            "--script=./mpv-scripts/sponsorblock_minimal.lua",
        ],
    }

    @classmethod
    def update(cls, **kwargs):
        for key, value in kwargs.items():
            if key in cls._settings:
                cls._settings[key] = value
            else:
                raise KeyError(f"'{key}' is not a valid configuration setting.")

    @classmethod
    def get(cls, key):
        return cls._settings.get(key)

    @classmethod
    def get_all_settings(cls):
        return cls._settings.copy()


class TermuxPlayerConfig(PlayerConfig):
    _settings = PlayerConfig._settings.copy()
    _settings.update(
        {
            "monitor": 1,
            "open_app": True,
            "return_app": True,
            "mpv_fullscreen_playback": True,
            "touch_mouse_gestures": True,
        }
    )


class Player:
    def __init__(self, url, args=None):
        self.url = url

        mpv_input_config_path = "./mpv-config/custom.conf"
        custom_input_config_exists = OSManager.exists(mpv_input_config_path)
        initial_args = []

        match (args, custom_input_config_exists):
            case (None, True):
                initial_args = [f"--input-conf={mpv_input_config_path}"]
            case (None, False):
                initial_args = []
            case (provided_args, _):
                initial_args = provided_args

        mpv_args = PlayerConfig.get("mpv_args")

        self.args = mpv_args + initial_args
        self.command = ["mpv"] + self.args + [self.url]

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
        SubprocessHelper.app_subprocess_help(
            self.command,
            "MPV",
            note="\nSee https://mpv.io/installation/\nIf using MPV via Termux, use MPV-X: pkg install mpv-x",
        )

    def run_mpv_android(
        self,
    ):  # require https://github.com/mpv-android/mpv-android/pull/58
        SubprocessHelper.app_subprocess_help(
            self.android_command, note="Current OS may not be Android."
        )

    def run_mpv_x(self):
        config = TermuxPlayerConfig.get_all_settings()

        mpv_args = self.args.copy()

        os.environ["DISPLAY"] = f":{config['monitor']}"

        if config["mpv_fullscreen_playback"] is True and "--fs" not in mpv_args:
            mpv_args.append("--fs")

        if config["touch_mouse_gestures"]:
            gestures_args = [
                "--no-window-dragging",
                "--script=./mpv-scripts/gestures.lua",
            ]

            for arg in gestures_args:
                if arg not in mpv_args:
                    mpv_args.append(arg)

        mpv_command = ["mpv"] + mpv_args + [self.url]

        termux_x11_command = ["am", "start", "-n", "com.termux.x11/.MainActivity"]
        termux_command = [
            "am",
            "start",
            "-n",
            "com.termux/com.termux.app.TermuxActivity",
        ]

        if config["open_app"]:
            SubprocessHelper.app_subprocess_help(termux_x11_command, "termux-x11")

        SubprocessHelper.app_subprocess_help(mpv_command)

        if config["return_app"]:
            SubprocessHelper.app_subprocess_help(termux_command, "termux")

    def classic_start(self):
        if OSManager.android_check():
            self.run_mpv_android()
        else:
            self.run_mpv()

    @classmethod
    def start_with_mode(cls, url, opts="auto"):
        print("Playing...")

        player = cls(url)

        match opts:
            case "auto":
                player.classic_start()
            case "android":
                player.run_mpv_android()
            case "ssh":
                print("Copy one of the commands below:")
                print(
                    f"MPV: \n\n\t{shlex.join(player.command)}\n\nMPV Android: \n\n\t{shlex.join(player.android_command)}\n\n"
                )
                InputHandler.press_any_key()
            case "termux-x11":
                player.run_mpv_x()
            case _:
                player.run_mpv()
