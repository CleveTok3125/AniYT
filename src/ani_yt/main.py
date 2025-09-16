# `main` contains the main logic to run the program, but not the interface.
# To use, import as a module and implement the interface or use the available *_interface

import os

from .bookmarking_handler import BookmarkingHandler
from .data_processing import DataProcessing
from .display import Display_Options, DisplayMenu
from .exceptions import MissingChannelUrl
from .file_handler import FileHandler, FileSourceHandler
from .history_handler import HistoryHandler
from .os_manager import OSManager
from .player import Player
from .query import Query
from .yt_dlp_handler import YT_DLP, YT_DLP_Options


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

        # find playlist index in history
        p_idx = next(
            (
                i
                for i, p in enumerate(history.get("playlists", []))
                if p.get("playlist_url") == curr_playlist_url
            ),
            None,
        )
        if p_idx is None:
            # If playlist not present, create and append
            playlist_entry = {
                "playlist_title": history["current"].get("playlist_title", ""),
                "playlist_url": curr_playlist_url,
                "videos": new_videos,
            }
            history.setdefault("playlists", []).append(playlist_entry)
        else:
            # merge videos into existing playlist
            old_videos = history["playlists"][p_idx].get("videos", [])
            merged = self.dp.merge_list(old_videos, new_videos, truncate=True)
            history["playlists"][p_idx]["videos"] = merged

        # persist: update entire playlists (and keep current)
        self.history_handler.update(
            curr=history.get("current"), playlists=history.get("playlists")
        )

        print("Done!")
        return

    def update_multiple(self, channel_urls, no_update_history=False):
        print("Getting playlist from multiple channels...")
        merged_playlist_videos = []  # list of Video dict (for merged video playlist)
        merged_playlist_lists = []  # list of [title, url] for file_handler cache

        for ch_url in channel_urls:
            try:
                dlp = YT_DLP(ch_url, self.ydl_options)
                playlist_data = dlp.get_playlist()
                playlist_videos = self.dp.omit(playlist_data)  # List[Video]

                # Merge preserving order of merged_playlist_videos: append only new video URLs
                merged_playlist_videos = self.dp.merge_list_preserve_order(
                    merged_playlist_videos, playlist_videos
                )

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

        p_idx = self._find_playlist_index(history, curr_playlist_url)
        if p_idx is None:
            playlist_entry = {
                "playlist_title": curr.get("playlist_title", ""),
                "playlist_url": curr_playlist_url,
                "videos": new_videos,
            }
            history.setdefault("playlists", []).append(playlist_entry)
        else:
            old_videos = history["playlists"][p_idx].get("videos", [])
            merged = self.dp.merge_list(old_videos, new_videos, truncate=True)
            history["playlists"][p_idx]["videos"] = merged

        self._history_update(
            curr=history.get("current"), playlists=history.get("playlists")
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

    def _videos_to_pairs(self, videos):
        # Convert List[Video] -> [[video_title, video_url], ...]
        return [[v.get("video_title", ""), v.get("video_url", "")] for v in videos]

    def start_player(self, url=None):
        if url:
            self.url = url
        Player.start_with_mode(url=self.url, opts=self.opts)

    def loop(self):
        while True:
            history = HistoryHandler().load()

            curr = history.get("current", {})

            curr_playlist_url = curr.get("playlist_url")
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

            videos = history["playlists"][p_idx].get("videos", [])
            menu_items = self._videos_to_pairs(videos)

            title, self.url = self.display_menu.choose_menu(menu_items)
            self.start_player()

            self.display_menu.mark_viewed(self.url)

    def menu(self, playlist_list):
        if not playlist_list:
            print("No playlist provided.")
            return

        playlist_title, playlist_url = self.display_menu.choose_menu(playlist_list)

        try:
            video_data = self.dlp.get_video(playlist_url)
        except MissingChannelUrl:
            print("Failed to fetch playlist videos.")
            return

        videos = self.dp.omit(video_data)  # List[Video]

        videos = self.dp.sort(videos, key=lambda x: x["video_title"])

        menu_items = self._videos_to_pairs(videos)
        title, self.url = self.display_menu.choose_menu(
            menu_items, clear_choosed_item=True
        )

        history = (
            self.history_handler.load()
            if self.history_handler.is_history()
            else {"current": {}, "playlists": []}
        )
        curr_obj = {
            "video_title": title,
            "video_url": self.url,
            "playlist_title": playlist_title,
            "playlist_url": playlist_url,
        }

        # find playlist index or create
        p_idx = next(
            (
                i
                for i, p in enumerate(history.get("playlists", []))
                if p.get("playlist_url") == playlist_url
            ),
            None,
        )
        if p_idx is None:
            history.setdefault("playlists", []).append(
                {
                    "playlist_title": playlist_title,
                    "playlist_url": playlist_url,
                    "videos": videos,
                }
            )
        else:
            old_videos = history["playlists"][p_idx].get("videos", [])
            merged = self.dp.merge_list(old_videos, videos, truncate=False)
            history["playlists"][p_idx]["videos"] = merged

        self.history_handler.update(curr=curr_obj, playlists=history.get("playlists"))

        self.start_player()

        self.display_menu.mark_viewed(self.url)

        self.loop()

    def show_bookmark(self):
        bms = self.bookmarking_handler.load()
        for key, value in bms.items():
            print(
                f"{self.display_menu.YELLOW}{key}{self.display_menu.RESET}\n\t{value}"
            )

    def list(self):
        playlist_list = self.load_playlist()  # should be list of [title,url]
        if not playlist_list:
            print("No cached playlists found.")
            return
        self.menu(playlist_list)

    def resume(self):
        history = HistoryHandler().load()
        curr = history.get("current", {})
        self.url = curr.get("video_url")

        if not self.url:
            print("No current video in history.")
            return

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
        video_data = self.dlp.get_video(url)
        videos = self.dp.omit(video_data)  # List[Video]
        videos = self.dp.sort(videos, key=lambda x: x["video_title"])
        menu_items = self._videos_to_pairs(videos)
        if not menu_items:
            print("No videos found in this playlist.")
            return
        _, self.url = self.display_menu.choose_menu(menu_items)
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
