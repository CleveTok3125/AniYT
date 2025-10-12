from datetime import datetime

from ..bookmarking_handler import BookmarkingHandler
from ..common import Typing
from ..exceptions import CategoryNotExist, PauseableException
from ..history_handler import HistoryHandler
from ..input_handler import InputHandler, ReturnCode
from ..os_manager import OSManager
from ..player import Player
from ..yt_dlp_handler import YT_DLP, YT_DLP_Options


class HistoryExtension:
    def _init_history(self):
        self.history_map = {}
        self._load_history_map()

    def _load_history_map(self):
        if (
            not hasattr(self, "history_handler")
            or not self.history_handler
            or not self.history_handler.is_history()
        ):
            return

        try:
            history = self.history_handler.load()
            # Build video_url -> status map
            self.history_map = {
                video["video_url"]: video.get("status", "")
                for playlist in history.get("playlists", [])
                for video in playlist.get("videos", [])
            }
        except Exception:
            self.history_map = {}

    def mark_viewed(self, url: str):
        """
        Mark the video as viewed in both history file and local map, and update last_viewed timestamp.
        """
        history = self.history_handler.load()

        p_idx, v_idx = self.history_handler.search(url, history)
        if p_idx != -1 and v_idx != -1:
            history["playlists"][p_idx]["videos"][v_idx]["status"] = "viewed"

            now = datetime.now().astimezone().isoformat()
            history["playlists"][p_idx]["videos"][v_idx]["last_viewed"] = now

            # persist
            self.history_handler.update(
                curr=history.get("current"), playlists=history.get("playlists")
            )
            # update local map
            self.history_map[url] = "viewed"

    def remove_viewed_status(self, url: str):
        """
        Remove the 'viewed' status from a video.
        """
        history = self.history_handler.load()
        p_idx, v_idx = self.history_handler.search(url, history)
        if p_idx != -1 and v_idx != -1:
            video = history["playlists"][p_idx]["videos"][v_idx]
            if "status" in video:
                video["status"] = ""
            if "last_viewed" in video:
                del video["last_viewed"]

            self.history_handler.update(
                curr=history.get("current"), playlists=history.get("playlists")
            )
            self.history_map[url] = ""

    def toggle_viewed_status(self, url: str):
        """
        Toggle the 'viewed' status of a video.
        If it's viewed, un-view it. If it's not viewed, mark it as viewed.
        """
        current_status = self.history_map.get(url, "").lower()
        if current_status == "viewed":
            self.remove_viewed_status(url)
        else:
            self.mark_viewed(url)

    def find_first_unviewed_index(self):
        if not hasattr(self, "data") or not self.data:
            return 0

        for idx, video in enumerate(self.data):
            if self.history_map.get(video["video_url"], "").lower() != "viewed":
                return idx
        return 0

    def find_next_unviewed_index(self, start_idx=0):
        if not self.data:
            return 0
        for idx in range(start_idx, len(self.data)):
            if (
                self.history_map.get(self.data[idx]["video_url"], "").lower()
                != "viewed"
            ):
                return idx

        for idx in range(0, start_idx):
            if (
                self.history_map.get(self.data[idx]["video_url"], "").lower()
                != "viewed"
            ):
                return idx
        return 0


class InputExtension:
    def _init_input_handler(self):
        self.input_handler = InputHandler()

    def map_user_input(self, prompt=None):
        user_input = self.input_handler.get_input(prompt).strip()

        input_map = {
            ReturnCode.NEXT_PAGE: "N",
            ReturnCode.PREV_PAGE: "P",
            ReturnCode.LINE_UP: "U",
            ReturnCode.LINE_DOWN: "D",
        }

        return input_map.get(user_input, user_input)

    def get_user_input(self):
        try:
            self.user_input = self.map_user_input()
        except KeyboardInterrupt:
            OSManager.exit(0)


class DisplayExtension(HistoryExtension, InputExtension):
    def _inject_dependencies(
        self,
    ):  # Only used when you want to declare an instance, other values ​​like str, int, list, etc can be taken directly from extra_opts
        self.bookmarking_handler = self._get_dependencies(
            "bookmark",
            BookmarkingHandler,
        )

        self.yt_dlp_opts = self._get_dependencies(
            "yt-dlp",
            YT_DLP_Options,
        )

        self.history_handler = self._get_dependencies(
            "history",
            HistoryHandler,
        )
        self._init_history()

        self._init_input_handler()

    def _init_extra_opts(self, extra_opts):
        self.extra_opts = extra_opts

        if not isinstance(extra_opts, dict):
            raise TypeError(
                f"The parameter passed should be a dictionary, but got {type(extra_opts)}"
            )

    def _get_dependencies(
        self, requirement: object, requirement_suggestion: type, fallback_factory=None
    ):
        dependency = self.extra_opts.get(requirement)

        if dependency is None:
            raise ValueError(f"Missing required dependency: {requirement}")
        if not isinstance(dependency, requirement_suggestion):
            raise TypeError(
                f"Dependency '{requirement}' must be an instance of {requirement_suggestion}"
            )

        return dependency

    def _update_bookmark(self, item, category, create_new=False):
        try:
            self.bookmarking_handler.update_item(
                item, category=category, create_new=create_new
            )
        except CategoryNotExist:
            pass

    def mark_bookmark(self, user_int, category, create_new=False):
        try:
            item: Typing.Video = self.data[user_int - 1]
            video_url = item["video_url"]

            if self.bookmarking_handler.is_item_exist(video_url, category=category):
                self.bookmarking_handler.remove_item(video_url, category=category)
            else:
                self._update_bookmark(item, category=category, create_new=create_new)
        except ValueError:
            PauseableException(
                "ValueError: only non-negative integers are accepted.", delay=-1
            )
        except IndexError:
            PauseableException(
                "IndexError: The requested item is not listed.", delay=-1
            )

    def is_item_bookmarked(self, item_url, category):
        return self.bookmarking_handler.is_item_exist(item_url, category=category)

    def open_image_with_mpv(self, url):
        Player.start_with_mode(url=url, opts=self.extra_opts.get("mode", "auto"))

    def show_thumbnail(self, user_int):
        item: Typing.Video = self.data[user_int - 1]
        url = item["video_url"]

        thumbnail_url = YT_DLP.standalone_get_thumbnail(url, self.yt_dlp_opts.ydl_opts)
        self.open_image_with_mpv(thumbnail_url)
