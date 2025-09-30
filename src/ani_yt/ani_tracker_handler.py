import subprocess
import sys
from pathlib import Path

from .helper import SubprocessHelper


class TrackerWrapper:
    @staticmethod
    def get_tracker_bin() -> Path:
        exe = "ani-tracker.exe" if sys.platform == "win32" else "ani-tracker"
        return (
            Path(sys.prefix) / ("Scripts" if sys.platform == "win32" else "bin") / exe
        )

    @staticmethod
    def print_help():
        SubprocessHelper.app_subprocess_help(
            [TrackerWrapper.get_tracker_bin(), "--help"]
        )

    @staticmethod
    def run_tracker(args):
        binary = TrackerWrapper.get_tracker_bin()
        if not binary.exists():
            print(
                f"Error: '{binary}' not found. Please install AniYT properly.",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            result = subprocess.run([str(binary)] + args)
            sys.exit(result.returncode)
        except KeyboardInterrupt:
            sys.exit(130)
