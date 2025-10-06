import argparse
import sys

from . import __version__
from .ani_tracker_handler import TrackerWrapper
from .extension import Extension
from .file_handler import Initialize
from .helper import IOHelper
from .main import Main
from .os_manager import OSManager
from .player import Termux_X11_OPTS


class ArgsHandler:
    @IOHelper.gracefully_terminate_exit
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Note: Options, if provided, will be processed sequentially in the order they are listed below."
        )

        self.parser.add_argument(
            "--full-help",
            action="store_true",
            help="show extended help for all commands and subcommands.",
        )

        self.parser.add_argument(
            "--version", action="store_true", help="show version and exit"
        )

        self.group_env = self.parser.add_argument_group("Environment Options")
        self.group_env.add_argument(
            "-t",
            "--temp",
            action="store_const",
            const="store_true",
            help="Use temporary folder (incompatible with -dir/--directory).",
        )
        self.group_env.add_argument(
            "-dir",
            "--directory",
            type=str,
            help="Specify working directory (incompatible with -t/--temp).",
        )
        self.group_env.add_argument(
            "-neu",
            "--no-extension-update",
            action="store_const",
            const="store_true",
            help="Disable extension update.",
        )

        self.group_update = self.parser.add_argument_group("Source Update Options")
        self.group_update.add_argument(
            "-su",
            "--source-update",
            action="store_const",
            const="source_update",
            help="Quick update command for `source update`",
        )
        self.group_update.add_argument(
            "-sr",
            "--source-rebuild",
            action="store_const",
            const="source_rebuild",
            help="Quick update command for `source rebuild`",
        )

        self.group_playlist = self.parser.add_argument_group(
            "Playlist and Channel Options"
        )
        self.group_playlist.add_argument(
            "-c",
            "--channel",
            type=str,
            help="Create or Update Playlist Data from Link, Channel ID, or Channel Handle.",
        )
        self.group_playlist.add_argument(
            "-mc",
            "--merge-channels",
            nargs="+",
            help="Merge playlists from multiple channels (URL, Channel ID, or handle).",
        )

        self.group_mpv = self.parser.add_argument_group("MPV Player Options")
        self.group_mpv.add_argument(
            "--mpv-player",
            type=str,
            choices=["auto", "default", "android", "ssh", "termux-x11"],
            default="auto",
            help="MPV player mode.",
        )

        self.group_cache = self.parser.add_argument_group("Cache and History Options")
        self.group_cache.add_argument(
            "--clear-cache",
            action="store_const",
            const="clear_cache",
            help="Clear cache.",
        )
        self.group_cache.add_argument(
            "--delete-history",
            action="store_const",
            const="delete_history",
            help="Delete history.",
        )
        self.group_cache.add_argument(
            "--clear-history",
            type=str,
            choices=["playlist", "videos", "unwatched"],
            help="Clear history: 'playlist' to remove old playlists, 'videos' to clear videos in old playlists, 'unwatched' to remove only unwatched videos.",
        )
        self.group_cache.add_argument(
            "--keep-recent",
            type=int,
            default=1,
            help="Number of recent playlists to keep when clearing history.",
        )
        self.group_cache.add_argument(
            "--delete-bookmark",
            action="store_const",
            const="delete_bookmark",
            help="Delete bookmark.",
        )

        self.group_browse = self.parser.add_argument_group("Browse and View Options")
        self.group_browse.add_argument(
            "-b",
            "--bookmark",
            action="store_const",
            const="bookmark",
            help="Show bookmark.",
        )
        self.group_browse.add_argument(
            "-l",
            "--list",
            action="store_const",
            const="list",
            help="Browse all cached playlists.",
        )
        self.group_browse.add_argument(
            "-v",
            "--viewed-mode",
            action="store_const",
            const="viewed_mode",
            help="Browse all videos in cached playlist.",
        )
        self.group_browse.add_argument(
            "-vr",
            "--viewed-refresh",
            action="store_const",
            const="viewed_refresh",
            help="Browse all videos in cached playlist and refresh it once.",
        )
        self.group_browse.add_argument(
            "-r",
            "--resume",
            action="store_const",
            const="resume",
            help="View last viewed video.",
        )

        self.subparsers = self.parser.add_subparsers(
            dest="command",
            help="Note: To avoid incorrect handling, positional arguments should be placed after all options.",
        )

        self.sources_parsers = self.subparsers.add_parser(
            "source", help="Manage channel source list."
        )
        self.sources_subparsers = self.sources_parsers.add_subparsers(
            dest="source_command"
        )

        add_parser = self.sources_subparsers.add_parser("add")
        add_parser.add_argument(
            "urls", nargs="+", help="One or more channel URLs or IDs to add"
        )

        remove_parser = self.sources_subparsers.add_parser("remove")
        remove_parser.add_argument(
            "urls", nargs="+", help="One or more channel URLs or IDs to remove"
        )

        self.sources_subparsers.add_parser(
            "template", help="Create placeholder source file."
        )

        self.sources_subparsers.add_parser(
            "update", help="Update playlist from all saved sources."
        )

        self.sources_subparsers.add_parser(
            "rebuild",
            help="Rebuild playlist from all saved sources (clear then update).",
        )

        self.download_parsers = self.subparsers.add_parser(
            "download", help="Download video and skip sponsors using SponsorBlock."
        )
        self.download_parsers.add_argument("url", type=str, help="Video url.")
        self.download_parsers.add_argument(
            "-cat",
            "--category",
            type=str,
            default="all",
            help="See https://wiki.sponsor.ajay.app/w/Types#Category.",
        )
        self.download_parsers.add_argument(
            "-m",
            "--mpv",
            action="store_const",
            const="mpv",
            help="Open downloaded video with MPV. Download progress will not be displayed.",
        )

        self.mpv_parsers = self.subparsers.add_parser("mpv", help="Open with MPV.")
        self.mpv_parsers.add_argument(
            "input",
            type=str,
            help="Video url or file path. File path are currently not supported on Android.",
        )

        self.termux_x11_options = self.parser.add_argument_group("Termux-X11 options")

        self.termux_x11_options.add_argument(
            "--monitor",
            type=int,
            default=Termux_X11_OPTS.monitor,
            help=f"X server monitor number (default: {Termux_X11_OPTS.monitor})",
        )

        self.termux_x11_options.add_argument(
            "--open-app",
            dest="open_app",
            action="store_true",
            default=Termux_X11_OPTS.open_app,
            help=f"Enable auto-opening Termux-X11 app (default: {Termux_X11_OPTS.open_app})",
        )
        self.termux_x11_options.add_argument(
            "--no-open-app",
            dest="open_app",
            action="store_false",
            help="Disable auto-opening Termux-X11 app.",
        )

        self.termux_x11_options.add_argument(
            "--return-app",
            dest="return_app",
            action="store_true",
            default=Termux_X11_OPTS.return_app,
            help=f"Enable auto-return Termux after playback (default: {Termux_X11_OPTS.return_app})",
        )
        self.termux_x11_options.add_argument(
            "--no-return-app",
            dest="return_app",
            action="store_false",
            help="Disable auto-return Termux after playback.",
        )

        self.termux_x11_options.add_argument(
            "--fullscreen",
            dest="fullscreen",
            action="store_true",
            default=Termux_X11_OPTS.mpv_fullscreen_playback,
            help=f"Enable fullscreen playback (default: {Termux_X11_OPTS.mpv_fullscreen_playback})",
        )
        self.termux_x11_options.add_argument(
            "--no-fullscreen",
            dest="fullscreen",
            action="store_false",
            help="Disable fullscreen playback.",
        )

        self.termux_x11_options.add_argument(
            "--gestures",
            dest="gestures",
            action="store_true",
            default=Termux_X11_OPTS.touch_mouse_gestures,
            help=f"Enable MPV touch/mouse gestures (default: {Termux_X11_OPTS.touch_mouse_gestures})",
        )
        self.termux_x11_options.add_argument(
            "--no-gestures",
            dest="gestures",
            action="store_false",
            help="Disable MPV touch/mouse gestures.",
        )

        self.search_parsers = self.subparsers.add_parser(
            "search", help="Search for a playlist."
        )
        self.search_parsers.add_argument("query", type=str, help="Search content.")
        self.search_parsers.add_argument(
            "-C", "--case-sensitive", action="store_true", help="Case sensitive."
        )
        self.search_parsers.add_argument(
            "-fs", "--fuzzysearch", action="store_true", help="Fuzzy search."
        )
        self.search_parsers.add_argument(
            "-s",
            "--score",
            type=int,
            default=50,
            help="The accuracy of fuzzy search (0-100).",
        )

        self.playlist_parsers = self.subparsers.add_parser(
            "playlist", help="Open playlist from URL"
        )

        self.playlist_parsers.add_argument("url", type=str)

        self._args_wrapping()

        self.args = self.parser.parse_args()

        self._argument_preprocessing()

    @IOHelper.gracefully_terminate
    def print_version(self):
        print(f"AniYT {__version__}")
        sys.exit(0)

    @IOHelper.gracefully_terminate
    def print_full_help(self):
        self.parser.print_help()

        for name, subparser in self.subparsers.choices.items():
            print(f"\nSubcommand: {name}")
            subparser.print_help()

        TrackerWrapper.print_help()

        sys.exit(0)

    def _args_wrapping(self):
        # Special arguments for wrapping, which need to be run before argsparse
        # By default, it needs to exit after running or there are additional steps to avoid invalid choice

        if len(sys.argv) > 1 and sys.argv[1] == "tracker":
            tracker_args = sys.argv[2:]
            TrackerWrapper.run_tracker(tracker_args)

            OSManager.exit(0)

    def _argument_preprocessing(self):
        # Parameters that need to be processed immediately upon launch

        if self.args.version:
            self.print_version()

        if self.args.full_help:
            self.print_full_help()

        if self.args.temp and self.args.directory:
            print(
                "Error: Cannot use both -t/--temp and -dir/--directory at the same time."
            )
            OSManager.exit(1)

        if self.args.temp:
            temp_path = OSManager.temporary_session()
            print(f"[Temp Mode] Using temporary directory: {temp_path}")

        if self.args.directory:
            directory, abs_path = OSManager.working_directory(self.args.directory)
            if abs_path:
                print(
                    f"[Custom Directory] Working directory set to: {directory} ({abs_path})"
                )
            else:
                print("The specified path is not a directory or does not exist.")
                OSManager.exit(404)

        Initialize.directory(make_parent=not self.args.directory)

        if self.args.no_extension_update:
            Extension.check_update_enabled = False

        if self.args.mpv_player == "termux-x11":
            if self.args.monitor < 1:
                print("Error: Monitor number must be >= 1")
                OSManager.exit(1)

            Termux_X11_OPTS.monitor = self.args.monitor
            Termux_X11_OPTS.open_app = self.args.open_app
            Termux_X11_OPTS.return_app = self.args.return_app
            Termux_X11_OPTS.mpv_fullscreen_playback = self.args.fullscreen
            Termux_X11_OPTS.touch_mouse_gestures = self.args.gestures

        self.main = Main(
            channel_url=self.args.channel,
            opts=self.args.mpv_player,
        )

        if self.args.channel:
            self.main.update()

        if self.args.merge_channels:
            self.main.update_multiple(self.args.merge_channels)

        if self.args.clear_history:
            self.main.clear_history(
                mode=self.args.clear_history, keep_recent=self.args.keep_recent
            )

        self.actions = {
            "clear_cache": self.main.clear_cache,
            "delete_history": self.main.delete_history,
            "delete_bookmark": self.main.delete_bookmark,
            "bookmark": self.main.show_bookmark,
            "list": self.main.list,
            "viewed_mode": self.main.loop,
            "viewed_refresh": self.main.loop_refresh,
            "resume": self.main.resume,
            "source_update": self.main.source_update,
            "source_rebuild": self.main.source_rebuild,
        }

    @IOHelper.gracefully_terminate_exit
    def run_main(self, action):
        try:
            return self.actions.get(action)()
        except TypeError as e:
            # print(e)
            raise TypeError(e)
            OSManager.exit(404)

    @IOHelper.gracefully_terminate_exit
    def listener(self):
        action_lst = [
            getattr(self.args, item, None) for item in list(self.actions.keys())
        ]

        if len(sys.argv) == 1:
            self.parser.print_help()
            OSManager.exit(0)

        if self.args.command == "source":
            actions = {
                "add": lambda: self.main.source_add(*self.args.urls),
                "remove": lambda: self.main.source_remove(*self.args.urls),
                "template": self.main.source_template,
                "update": self.main.source_update,
                "rebuild": self.main.source_rebuild,
            }
            action = actions.get(self.args.source_command)
            if action:
                action()

        for action in action_lst:
            if action:
                self.run_main(action)

        if self.args.command == "download":
            self.main.download(self.args.url, self.args.category, self.args.mpv)

        if self.args.command == "mpv":
            self.main.open_with_mpv(self.args.input)

        if self.args.command == "search":
            self.main.search(
                self.args.query,
                self.args.case_sensitive,
                fuzzy=self.args.fuzzysearch,
                score=self.args.score,
            )

        if self.args.command == "playlist":
            self.main.playlist_from_url(self.args.url)

        OSManager.exit(0)
