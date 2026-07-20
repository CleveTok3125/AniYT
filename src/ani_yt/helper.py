import functools
import os.path
import shutil
import subprocess
import sys

import ujson as json


def get_script_name():
    return os.path.basename(sys.argv[0])


class IOHelper:
    @staticmethod
    def gracefully_terminate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                print("Action canceled by user.")

        return wrapper

    @staticmethod
    def gracefully_terminate_exit(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                print("Action canceled by user.")
                sys.exit(0)

        return wrapper


class SubprocessHelper:
    @staticmethod
    @IOHelper.gracefully_terminate
    def require_app(commands, app_name=None, *, check_only=False, note=""):
        if not SubprocessHelper.app_subprocess_help(commands, app_name, check_only=check_only, note=note):
            sys.exit(127)

    @staticmethod
    def app_subprocess_help(commands, app_name=None, *, check_only=False, note=""):
        if isinstance(commands, (list, tuple)) and commands:
            cmd_name = commands[0]
            cmd_list = list(commands)
        elif isinstance(commands, str):
            cmd_name = commands
            cmd_list = [commands]
        else:
            print(f"Expected list, tuple or str, but received {type(commands).__name__}")
            return False

        if app_name is None:
            app_name = cmd_name

        if shutil.which(cmd_name) is None:
            print(f"{app_name} is not installed. Please install before running.{' ' if note else ''}{note}")
            return False

        if check_only:
            return True

        try:
            subprocess.run(cmd_list, check=True)
            return True
        except FileNotFoundError:
            print(f"Error: {cmd_name} could not be found when running.{' ' if note else ''}{note}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"Error running {app_name}: {e}")
            return False


class LegacyCompatibility:
    @staticmethod
    def normalize_playlist(
        playlist: list[tuple[str, str]] | list[dict[str, str]] | list[list[str]],
    ) -> list[dict[str, str]]:
        if not playlist:
            return []

        # Legacy: list[tuple[str, str]]
        if isinstance(playlist[0], (tuple, list)):
            return [{"video_title": t, "video_url": u, "status": ""} for t, u in playlist]

        # New: list[dict]
        if isinstance(playlist[0], dict):
            normalized = []
            for v in playlist:
                assert isinstance(v, dict)
                v_copy = dict(v)
                if "status" not in v_copy:
                    v_copy["status"] = ""
                normalized.append(v_copy)
            return normalized

        raise TypeError("Unsupported playlist format")


class FormatHelper:
    @staticmethod
    def beautify_json(json_str):
        return json.dumps(json_str, indent=4, ensure_ascii=False)
