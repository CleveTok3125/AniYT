import argparse
import os
import sys

# Custom lib
# from extension import Extension
from .exceptions import MissingChannelUrl, InvalidHistoryFile
from .os_manager import OSManager
from .data_processing import DataProcessing
from .query import Query
from .file_handler import FileHandler, FileSourceHandler
from .history_handler import HistoryHandler
from .bookmarking_handler import BookmarkingHandler
from .yt_dlp_handler import YT_DLP_Options, YT_DLP
from .player import Player, Termux_X11_OPTS
from .display import (
    Display_Options,
    Display,
    DisplayExtensionFallback,
    DisplayExtension,
    DisplayMenu,
)


class Main:
    def __init__(self, channel_url, opts="auto"):
        self.opts = opts.lower()
        self.ydl_options = YT_DLP_Options()
        self.dlp = YT_DLP(channel_url, self.ydl_options)
        self.file_handler = FileHandler()
        self.history_handler = HistoryHandler()
        self.bookmarking_handler = BookmarkingHandler()
        self.dp = DataProcessing
        self.display_opts = Display_Options()
        self.display_menu = DisplayMenu(
            self.display_opts,
            extra_opts={
                "yt-dlp": self.ydl_options,
                "mode": self.opts,
                "bookmark": self.bookmarking_handler,
            },
        )
        self.url = ""

    def source_add(self, *urls):
        added = FileSourceHandler().add_sources(*urls)
        print(f"\nSource Manager: Added {added} new sources.\n")

    def source_remove(self, *urls):
        removed = FileSourceHandler().remove_sources(*urls)
        print(f"\nSource Manager: Removed {removed} sources.\n")

    def source_template(self):
        FileSourceHandler().placeholder()
        print("\nSource Manager: Template created.\n")

    def _source_load_helper(self):
        fsh = FileSourceHandler()
        sources = fsh.load()
        if not sources:
            print("\nSource Manager: No sources to update.\n")
            return
        return sources

    def source_update(self):
        sources = self._source_load_helper()

        if not sources:
            return

        self.update_multiple(sources)

    def source_rebuild(self):
        print("Rebuilding playlist from sources...")
        self.file_handler.dump([])
        sources = self._source_load_helper()

        if not sources:
            return

        self.update_multiple(sources, no_update_history=True)
        print("Rebuild complete!")

    def update(self):
        print("Getting playlist...")
        try:
            playlist = self.dlp.get_playlist()
            print("Saving...")
            playlist = self.dp.omit(playlist)
            self.file_handler.dump(playlist)
            print("Done!")
        except MissingChannelUrl:
            print(
                f"Playlist info or channel not found.\nTo get playlist info: {os.path.basename(__file__)} -c/--channel CHANNEL"
            )
            OSManager.exit(404)

        if not self.history_handler.is_history():
            return

        print("Update history playlist...")
        history = self.history_handler.load()
        new_playlist = self.dlp.get_video(list(history["playlist"].values())[0])
        print("Saving...")
        new_playlist = self.dp.omit(new_playlist)
        new_playlist = self.dp.merge_list(history["videos"], new_playlist)
        self.history_handler.update(
            history["current"], history["playlist"], new_playlist
        )
        print("Done!")
        return

    def update_multiple(self, channel_urls, no_update_history=False):
        print("Getting playlist from multiple channels...")
        merged_playlist = []
        for ch_url in channel_urls:
            try:
                dlp = YT_DLP(ch_url, self.ydl_options)
                playlist = dlp.get_playlist()
                playlist = self.dp.omit(playlist)
                merged_playlist = self.dp.merge_list_preserve_order(
                    merged_playlist, playlist
                )
            except MissingChannelUrl:
                print(f"Channel not found: {ch_url}")
                continue
        print("Saving merged playlist...")
        self.file_handler.dump(merged_playlist)
        print("Done!")

        if no_update_history or not self.history_handler.is_history():
            return

        print("Update history playlist...")
        history = self.history_handler.load()
        new_playlist = YT_DLP.standalone_get_video(
            list(history["playlist"].values())[0], self.ydl_options.ydl_opts
        )
        print("Saving...")
        new_playlist = self.dp.omit(new_playlist)
        new_playlist = self.dp.merge_list(history["videos"], new_playlist)
        self.history_handler.update(
            history["current"], history["playlist"], new_playlist
        )
        print("Done!")

    def clear_cache(self):
        self.file_handler.clear_cache()

    def delete_history(self):
        self.history_handler.delete_history()

    def delete_bookmark(self):
        self.bookmarking_handler.delete_bookmark()

    def load_playlist(self):
        try:
            playlist = self.file_handler.load()
        except FileNotFoundError:
            self.update()
            playlist = self.file_handler.load()
        return playlist

    def start_player(self, url=None):
        if url:
            self.url = url
        Player.start_with_mode(url=self.url, opts=self.opts)

    def loop(self):
        while True:
            history = HistoryHandler().load()
            videos = history["videos"]
            title, self.url = self.display_menu.choose_menu(videos)
            self.start_player()
            index = self.history_handler.search(self.url, history)
            if len(videos[index]) == 2:
                videos[index] += ("viewed",)
            self.history_handler.update({title: self.url}, None, videos)

    def menu(self, video):
        playlist_title, url = self.display_menu.choose_menu(video)
        video = self.dlp.get_video(url)
        video = self.dp.omit(video)
        videos = self.dp.sort(video)
        title, self.url = self.display_menu.choose_menu(videos, clear_choosed_item=True)
        self.history_handler.update({title: self.url}, {playlist_title: url}, videos)
        self.start_player()
        history = HistoryHandler().load()
        videos = history["videos"]
        index = self.history_handler.search(self.url, history)
        videos[index] += ("viewed",)
        self.history_handler.update({title: self.url}, None, videos)
        self.loop()

    def show_bookmark(self):
        bms = self.bookmarking_handler.load()
        for key, value in bms.items():
            print(
                f"{self.display_menu.YELLOW}{key}{self.display_menu.RESET}\n\t{value}"
            )

    def list(self):
        playlist = self.load_playlist()
        self.menu(playlist)

    def resume(self):
        history = HistoryHandler().load()
        history = history["current"]
        self.url = list(history.values())[0]
        self.start_player()
        self.loop()

    def search(self, inp, case_sensitive=False, fuzzy=False, score=50):
        if not inp.strip():
            print("Empty search query.")
            OSManager.exit(0)

        query = Query(CASE=case_sensitive)
        playlist = self.load_playlist()
        if fuzzy:
            playlist = query.fuzzysearch(playlist, inp, score)
        else:
            playlist = query.search(playlist, inp)

        if not playlist:
            print("No matching playlist found.")
            return
        self.menu(playlist)

    def playlist_from_url(self, url):
        video = self.dlp.get_video(url)
        video = self.dp.omit(video)
        videos = self.dp.sort(video)
        _, self.url = self.display_menu.choose_menu(videos)
        self.start_player()

    def download(self, url, category, mpv):
        capture_output = mpv == "mpv"
        result = YT_DLP.download(url, category, capture_output=capture_output)

        if OSManager.android_check():
            return

        if result and capture_output:
            result = result.decode().split("\r")[-1].strip()
            self.start_player(result)
        elif not result and not capture_output:
            pass
        else:
            print(
                "No data returned. There was an error downloading the video or it was already downloaded."
            )

    def open_with_mpv(self, inp):
        self.start_player(inp)


class ArgsHandler:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Note: Options, if provided, will be processed sequentially in the order they are listed below."
        )

        self.parser.add_argument(
            "-t",
            "--temp",
            action="store_const",
            const="store_true",
            help="Use temporary folder (incompatible with -dir/--directory).",
        )
        self.parser.add_argument(
            "-dir",
            "--directory",
            type=str,
            help="Specify working directory (incompatible with -t/--temp).",
        )
        self.parser.add_argument(
            "-neu",
            "--no-extension-update",
            action="store_const",
            const="store_true",
            help="Disable extension update.",
        )

        self.parser.add_argument(
            "-su",
            "--source-update",
            action="store_const",
            const="source_update",
            help="Quick update command for `source update`",
        )

        self.parser.add_argument(
            "-sr",
            "--source-rebuild",
            action="store_const",
            const="source_rebuild",
            help="Quick update command for `source rebuild`",
        )

        self.parser.add_argument(
            "-c",
            "--channel",
            type=str,
            help="Create or Update Playlist Data from Link, Channel ID, or Channel Handle.",
        )
        self.parser.add_argument(
            "-mc",
            "--merge-channels",
            nargs="+",
            help="Merge playlists from multiple channels (URL, Channel ID, or handle).",
        )
        self.parser.add_argument(
            "--mpv-player",
            type=str,
            choices=["auto", "default", "android", "ssh", "termux-x11"],
            default="auto",
            help="MPV player mode.",
        )
        self.parser.add_argument(
            "--clear-cache",
            action="store_const",
            const="clear_cache",
            help="Clear cache.",
        )
        self.parser.add_argument(
            "--delete-history",
            action="store_const",
            const="delete_history",
            help="Delete history.",
        )
        self.parser.add_argument(
            "--delete-bookmark",
            action="store_const",
            const="delete_bookmark",
            help="Delete bookmark.",
        )
        self.parser.add_argument(
            "-b",
            "--bookmark",
            action="store_const",
            const="bookmark",
            help="Show bookmark.",
        )
        self.parser.add_argument(
            "-l",
            "--list",
            action="store_const",
            const="list",
            help="Browse all cached playlists.",
        )
        self.parser.add_argument(
            "-v",
            "--viewed-mode",
            action="store_const",
            const="viewed_mode",
            help="Browse all videos in cached playlist. Cached playlists will be cleared after playlist selection.",
        )
        self.parser.add_argument(
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

        self.termux_x11_parser = self.subparsers.add_parser(
            "termux-x11", help="Configure Termux-X11 MPV playback options."
        )

        self.termux_x11_parser.add_argument(
            "--monitor",
            type=int,
            default=Termux_X11_OPTS.monitor,
            help=f"X server monitor number (default: {Termux_X11_OPTS.monitor})",
        )

        self.termux_x11_parser.add_argument(
            "--open-app",
            dest="open_app",
            action="store_true",
            default=Termux_X11_OPTS.open_app,
            help=f"Enable auto-opening Termux-X11 app (default: {Termux_X11_OPTS.open_app})",
        )
        self.termux_x11_parser.add_argument(
            "--no-open-app",
            dest="open_app",
            action="store_false",
            help="Disable auto-opening Termux-X11 app.",
        )

        self.termux_x11_parser.add_argument(
            "--return-app",
            dest="return_app",
            action="store_true",
            default=Termux_X11_OPTS.return_app,
            help=f"Enable auto-return Termux after playback (default: {Termux_X11_OPTS.return_app})",
        )
        self.termux_x11_parser.add_argument(
            "--no-return-app",
            dest="return_app",
            action="store_false",
            help="Disable auto-return Termux after playback.",
        )

        self.termux_x11_parser.add_argument(
            "--fullscreen",
            dest="fullscreen",
            action="store_true",
            default=Termux_X11_OPTS.mpv_fullscreen_playback,
            help=f"Enable fullscreen playback (default: {Termux_X11_OPTS.mpv_fullscreen_playback})",
        )
        self.termux_x11_parser.add_argument(
            "--no-fullscreen",
            dest="fullscreen",
            action="store_false",
            help="Disable fullscreen playback.",
        )

        self.termux_x11_parser.add_argument(
            "--gestures",
            dest="gestures",
            action="store_true",
            default=Termux_X11_OPTS.touch_mouse_gestures,
            help=f"Enable MPV touch/mouse gestures (default: {Termux_X11_OPTS.touch_mouse_gestures})",
        )
        self.termux_x11_parser.add_argument(
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

        self.args = self.parser.parse_args()

        self._argument_preprocessing()

    def _argument_preprocessing(self):
        # Parameters that need to be processed immediately upon launch

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

        if self.args.no_extension_update:
            Extension.check_update_enabled = False

        if self.args.command == "termux-x11":
            if self.args.monitor < 1:
                print("Error: Monitor number must be >= 1")
                OSManager.exit(1)

            Termux_X11_OPTS.monitor = self.args.monitor
            Termux_X11_OPTS.open_app = self.args.open_app
            Termux_X11_OPTS.return_app = self.args.return_app
            Termux_X11_OPTS.fullscreen = self.args.fullscreen
            Termux_X11_OPTS.gestures = self.args.gestures

        self.main = Main(
            channel_url=self.args.channel,
            opts=self.args.mpv_player,
        )

        if self.args.channel:
            self.main.update()

        if self.args.merge_channels:
            self.main.update_multiple(self.args.merge_channels)

        self.actions = {
            "clear_cache": self.main.clear_cache,
            "delete_history": self.main.delete_history,
            "delete_bookmark": self.main.delete_bookmark,
            "bookmark": self.main.show_bookmark,
            "list": self.main.list,
            "viewed_mode": self.main.loop,
            "resume": self.main.resume,
            "source_update": self.main.source_update,
            "source_rebuild": self.main.source_rebuild,
        }

    def run_main(self, action):
        try:
            return self.actions.get(action)()
        except TypeError as e:
            print(e)
            OSManager.exit(404)

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


def main():
    ArgsHandler().listener()


if __name__ == "__main__":
    main()
