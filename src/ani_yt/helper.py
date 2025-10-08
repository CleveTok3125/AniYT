import functools
import shutil
import subprocess
import sys
from typing import Dict, List, Tuple, Union


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
    def app_subprocess_help(commands, app_name=None, *, check_only=False, note=""):
        if isinstance(commands, (list, tuple)) and commands:
            cmd_name = commands[0]
            cmd_list = list(commands)
        elif isinstance(commands, str):
            cmd_name = commands
            cmd_list = [commands]
        else:
            print(
                f"Expected list, tuple or str, but received {type(commands).__name__}"
            )
            sys.exit(1)

        if app_name is None:
            app_name = cmd_name

        if shutil.which(cmd_name) is None:
            print(
                f"{app_name} is not installed. Please install before running.{' ' if note else ''}{note}"
            )
            sys.exit(127)

        if check_only:
            return

        try:
            subprocess.run(cmd_list, check=True)
        except FileNotFoundError:
            print(
                f"Error: {cmd_name} could not be found when running.{' ' if note else ''}{note}"
            )
            sys.exit(127)
        except subprocess.CalledProcessError as e:
            print(f"Error running {app_name}: {e}")
            sys.exit(e.returncode)


class LegacyCompatibility:
    @staticmethod
    def normalize_playlist(
        playlist: Union[List[Tuple[str, str]], List[Dict[str, str]]],
    ) -> List[Dict[str, str]]:
        if not playlist:
            return []

        # Legacy: list[tuple[str, str]]
        if isinstance(playlist[0], (tuple, list)):
            return [
                {"video_title": t, "video_url": u, "status": ""} for t, u in playlist
            ]

        # New: list[dict]
        if isinstance(playlist[0], dict):
            normalized = []
            for v in playlist:
                v_copy = dict(v)
                if "status" not in v_copy:
                    v_copy["status"] = ""
                normalized.append(v_copy)
            return normalized

        raise TypeError("Unsupported playlist format")
