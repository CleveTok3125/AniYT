import shutil
import subprocess
import sys


class SubprocessHelper:
    @staticmethod
    def app_subprocess_helper(commands, app_name=None, *, check_only=False, note=""):
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
            print(f"{app_name} is not installed. Please install before running.")
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
