# `main` contains the main logic to run the program, but not the interface.
# To use, import as a module and implement the interface or use the available *_interface

import os
from typing import List, Optional

from .bookmarking_handler import BookmarkingHandler
from .common import BookmarkData, Current, HistoryData, Playlist, Video
from .data_processing import DataProcessing
from .display import Display_Options, DisplayColor, DisplayMenu
from .exceptions import MissingChannelUrl
from .file_handler import FileHandler, FileSourceHandler
from .helper import IOHelper
from .history_handler import HistoryHandler
from .os_manager import OSManager
from .player import Player
from .query import Query
from .yt_dlp_handler import YT_DLP, YT_DLP_Options


class Main:
    def __init__(self, channel_url: str, opts: str = "auto"):
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
                "history": self.history_handler,
            },
        )
        self.url = ""

    @IOHelper.gracefully_terminate
    def source_add(self, *urls: str) -> None:
        added = FileSourceHandler().add_sources(*urls)
        print(f"\nSource Manager: Added {added} new sources.\n")

    @IOHelper.gracefully_terminate
    def source_remove(self, *urls: str) -> None:
        removed = FileSourceHandler().remove_sources(*urls)
        print(f"\nSource Manager: Removed {removed} sources.\n")

    @IOHelper.gracefully_terminate
    def source_template(self) -> None:
        FileSourceHandler().placeholder()
        print("\nSource Manager: Template created.\n")

    def _source_load_helper(self) -> Optional[List[str]]:
        fsh = FileSourceHandler()
        sources = fsh.load()
        if not sources:
            print("\nSource Manager: No sources to update.\n")
            return
        return sources

    @IOHelper.gracefully_terminate
    def source_update(self) -> None:
        sources = self._source_load_helper()

        if not sources:
            return

        self._update_multiple(sources)

    @IOHelper.gracefully_terminate
    def source_rebuild(self) -> None:
        print("Rebuilding playlist from sources...")
        self.file_handler.dump([])
        sources = self._source_load_helper()

        if not sources:
            return

        self._update_multiple(sources, no_update_history=True)
        print("Rebuild complete!")

    @IOHelper.gracefully_terminate
    def update(self) -> None:
        print("Getting playlist...")
        try:
            playlist_data = self.dlp.get_playlist()
            print("Saving...")
            playlist_videos = self.dp.omit(playlist_data)
            playlist_list = [
                [v["video_title"], v["video_url"]] for v in playlist_videos
            ]
            self.file_handler.dump(playlist_list)
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

        # Only update the current list being viewed. For other lists in the history, the function will be automatically called when switching viewing history.
        curr = history.get("current", {})
        curr_playlist_url = curr.get("playlist_url")
        if not curr_playlist_url:
            print("No current playlist set in history. Skipping history update.")
            return

        new_playlist_data = self.dlp.get_video(curr_playlist_url)
        print("Saving...")
        new_videos = self.dp.omit(new_playlist_data)  # List[Video]

        self.history_handler.update(curr=curr, videos=new_videos)

        print("Done!")
        return

    def _update_multiple(
        self, channel_urls: List[str], no_update_history: bool = False
    ) -> None:
        print("Getting playlist from multiple channels...")
        merged_playlist_lists: List[str, str] = (
            []
        )  # list of [title, url] for file_handler cache

        for ch_url in channel_urls:
            try:
                dlp = YT_DLP(ch_url, self.ydl_options)
                playlist_data = dlp.get_playlist()
                playlist_videos = self.dp.omit(playlist_data)  # List[Video]

                # For cache, operate on list-of-lists: map playlist_videos -> [[title,url],...]
                playlist_list = [
                    [v["video_title"], v["video_url"]] for v in playlist_videos
                ]
                merged_playlist_lists = self.dp.merge_list_preserve_order(
                    merged_playlist_lists, playlist_list
                )
            except MissingChannelUrl:
                print(f"Channel not found: {ch_url}")
                continue

        print("Saving merged playlist...")
        self.file_handler.dump(merged_playlist_lists)
        print("Done!")

        if no_update_history or not self.history_handler.is_history():
            return

        # Update history playlist similarly to update()
        print("Update history playlist...")
        history = self.history_handler.load()
        curr = history.get("current", {})
        curr_playlist_url = curr.get("playlist_url")
        if not curr_playlist_url:
            print("No current playlist set in history. Skipping history update.")
            return

        # get fresh videos for current history playlist
        new_playlist_data = YT_DLP.standalone_get_video(
            curr_playlist_url, self.ydl_options.ydl_opts
        )
        print("Saving...")
        new_videos = self.dp.omit(new_playlist_data)

        self.history_handler.update(curr=curr, videos=new_videos)
        print("Done!")

    @IOHelper.gracefully_terminate
    def clear_cache(self):
        self.file_handler.clear_cache()

    @IOHelper.gracefully_terminate
    def delete_history(self):
        self.history_handler.delete_history()

    @IOHelper.gracefully_terminate
    def clear_history(self, *args, **kwargs):
        self.history_handler.clear_history(*args, **kwargs)

    @IOHelper.gracefully_terminate
    def delete_bookmark(self):
        self.bookmarking_handler.delete_file()

    @IOHelper.gracefully_terminate_exit
    def load_playlist(self):
        try:
            playlist: Playlist = self.file_handler.load()
        except FileNotFoundError:
            self.update()
            playlist = self.file_handler.load()
        return playlist

    def _videos_to_pairs(self, videos: List[Video]) -> List[List[str]]:
        return [[v.get("video_title", ""), v.get("video_url", "")] for v in videos]

    @IOHelper.gracefully_terminate
    def start_player(self, url: str = None) -> None:
        if url:
            self.url = url
        Player.start_with_mode(url=self.url, opts=self.opts)

    def loop_refresh(self):
        self.loop(refresh=True)

    @IOHelper.gracefully_terminate_exit
    def loop(self, refresh: bool = False) -> None:
        while True:
            history: HistoryData = HistoryHandler().load()

            curr: Current = history.get("current", {})

            curr_playlist_url: str = curr.get("playlist_url")
            if not curr_playlist_url:
                print("No current playlist configured in history.")
                return

            p_idx = next(
                (
                    i
                    for i, p in enumerate(history.get("playlists", []))
                    if p.get("playlist_url") == curr_playlist_url
                ),
                None,
            )
            if p_idx is None:
                print("Current playlist not found in history.")
                return

            if refresh:
                try:
                    video_data = self.dlp.get_video(curr_playlist_url)
                except MissingChannelUrl:
                    print("Failed to fetch playlist videos.")
                    return

                videos = self.dp.omit(video_data)
                videos = self.dp.sort(videos, key=lambda x: x["video_title"])

                self.history_handler.update(curr=curr, videos=videos)
                history: HistoryData = self.history_handler.load()

            videos: Video = history["playlists"][p_idx].get("videos", [])
            menu_items: List[List[str]] = self._videos_to_pairs(videos)

            title, self.url = self.display_menu.choose_menu(menu_items)
            self.start_player()
            self.history_handler.update(curr=curr, viewed=True)
            self.display_menu.mark_viewed(self.url)

    @IOHelper.gracefully_terminate_exit
    def menu(self, playlist_list: List[List[str]]):
        if not playlist_list:
            print("No playlist provided.")
            return

        playlist_title, playlist_url = self.display_menu.choose_menu(playlist_list)

        try:
            video_data = self.dlp.get_video(playlist_url)
        except MissingChannelUrl:
            print("Failed to fetch playlist videos.")
            return

        videos: List[Video] = self.dp.omit(video_data)

        videos = self.dp.sort(videos, key=lambda x: x["video_title"])

        menu_items = self._videos_to_pairs(videos)
        title, self.url = self.display_menu.choose_menu(
            menu_items, clear_choosed_item=True
        )

        curr_obj = {
            "video_title": title,
            "video_url": self.url,
            "playlist_title": playlist_title,
            "playlist_url": playlist_url,
        }

        self.history_handler.update(curr=curr_obj, videos=videos, viewed=True)

        self.start_player()
        self.display_menu.mark_viewed(self.url)
        self.loop()

    @IOHelper.gracefully_terminate
    def show_bookmark(self):
        bms: BookmarkData = self.bookmarking_handler.load_full_data()
        for category in bms.keys():
            category_items = bms[category].items()
            if category_items:
                print(
                    f"{DisplayColor.BRIGHT_BLUE}{category.title()}{DisplayColor.RESET}"
                )
            for video_title, video_url in category_items:
                print(
                    f"{" " * 2}{DisplayColor.YELLOW}{video_title}{DisplayColor.RESET}\n{" " * 4}{DisplayColor.LINK_COLOR}{video_url}{DisplayColor.RESET}"
                )

    @IOHelper.gracefully_terminate_exit
    def list(self):
        playlist_list: List[str, str] = (
            self.load_playlist()
        )  # should be list of [title,url]
        if not playlist_list:
            print("No cached playlists found.")
            return
        self.menu(playlist_list)

    @IOHelper.gracefully_terminate_exit
    def resume(self):
        history: HistoryData = HistoryHandler().load()
        curr: Current = history.get("current", {})
        self.url = curr.get("video_url")

        if not self.url:
            print("No current video in history.")
            return

        self.start_player()
        self.loop()

    @IOHelper.gracefully_terminate_exit
    def search(
        self,
        inp: str,
        case_sensitive: bool = False,
        fuzzy: bool = False,
        score: int = 50,
    ) -> None:
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

    @IOHelper.gracefully_terminate_exit
    def playlist_from_url(self, url: str):
        video_data = self.dlp.get_video(url)
        videos: List[Video] = self.dp.omit(video_data)
        videos = self.dp.sort(videos, key=lambda x: x["video_title"])
        menu_items = self._videos_to_pairs(videos)
        if not menu_items:
            print("No videos found in this playlist.")
            return
        _, self.url = self.display_menu.choose_menu(menu_items)
        self.start_player()

    @IOHelper.gracefully_terminate_exit
    def download(self, url: str, category: str, mpv: str):
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

    @IOHelper.gracefully_terminate
    def open_with_mpv(self, url: str):
        self.start_player(url)
