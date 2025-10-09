from datetime import datetime
from typing import Dict, List, Literal, Optional

import ujson as json

from .common import Typing
from .data_processing import DataProcessing
from .exceptions import InvalidHistoryFile
from .os_manager import OSManager

VideoData = List[Typing.Video]
Playlist = Dict[str, object]  # keys: playlist_title, playlist_url, videos


class HistoryHandler:
    def __init__(self):
        self.filename = "./data/history.json"
        self.encoding = "utf-8"
        self.required_keys = {"current", "playlists"}

    def safe_history_load(func):
        def helper(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)

                if not isinstance(result, dict):
                    raise InvalidHistoryFile(self.filename)
                if not all(key in result for key in self.required_keys):
                    raise InvalidHistoryFile(self.filename)
                return result
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                raise InvalidHistoryFile(self.filename)

        return helper

    def is_history(self):
        return OSManager.exists(self.filename)

    @safe_history_load
    def load(self):
        with open(self.filename, "r", encoding=self.encoding) as f:
            return json.load(f)

    def update(
        self,
        curr: Optional[Dict] = None,
        playlists: Optional[List[Playlist]] = None,
        videos: Optional[VideoData] = None,
        viewed: bool = False,
        truncate: bool = True,
    ):
        """
        Update the history file.

        Parameters:
        - curr: Current playlist information (dict with 'playlist_title', 'playlist_url', etc.)
        - playlists: Optional list to replace/update all playlists.
        - videos: Optional list of new videos to merge into the current playlist.
        - viewed: If True, sets last_viewed timestamp for the current playlist.
        - truncate: If True, old videos not in new_videos are removed during merge.

        Behavior:
        1. If 'playlists' is provided, replaces the existing playlists.
        2. If 'curr' is provided:
           - Finds or creates the playlist corresponding to curr['playlist_url'].
           - If 'videos' is provided, merges them into the playlist and updates last_updated.
           - If 'viewed' is True, updates last_viewed.
        3. Saves the updated history file to disk.
        """

        # Load or initialize history
        if self.is_history():
            content = self.load()
        else:
            content = {"current": {}, "playlists": []}

        now = datetime.now().astimezone().isoformat()  # system timezone timestamp

        # Replace playlists if provided
        if playlists is not None:
            content["playlists"] = playlists

        # Update current playlist info
        if curr:
            content["current"] = curr
            playlist_url = curr.get("playlist_url")
            if playlist_url:
                # Find the current playlist in history
                playlist = next(
                    (
                        p
                        for p in content["playlists"]
                        if p.get("playlist_url") == playlist_url
                    ),
                    None,
                )

                if playlist is None:
                    # Playlist does not exist → create new entry
                    playlist = {
                        "playlist_title": curr.get("playlist_title", ""),
                        "playlist_url": playlist_url,
                        "videos": videos if videos else [],
                        "last_updated": now if videos else None,
                        "last_viewed": now if viewed else None,
                    }
                    content["playlists"].append(playlist)
                else:
                    # Playlist exists → merge videos if provided
                    if videos:
                        old_videos = playlist.get("videos", [])
                        playlist["videos"] = DataProcessing.merge_list(
                            old_videos, videos, truncate=truncate
                        )
                        playlist["last_updated"] = (
                            now  # always update when videos are merged
                        )

                    # Update last_viewed if user is currently watching
                    if viewed:
                        playlist["last_viewed"] = now

        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(content, f, indent=4)

    def search(self, curr_url, history):  # -> (playlist_index, video_index)
        if not isinstance(history, dict) or "playlists" not in history:
            raise InvalidHistoryFile(self.filename)

        for p_idx, playlist in enumerate(history["playlists"]):
            for v_idx, video in enumerate(playlist.get("videos", [])):
                if video.get("video_url") == curr_url:
                    return (p_idx, v_idx)
        return (-1, -1)

    def delete_history(self):
        OSManager.delete_file(self.filename)

    def clear_history(
        self,
        mode: Literal["playlist", "videos", "unwatched"] = "playlist",
        keep_recent: int = 1,
    ):
        """
        Clear old history based on timestamp.

        Parameters:
        - mode:
            "playlist"  -> delete full playlists
            "videos"    -> delete all videos in playlist
            "unwatched" -> delete only videos without 'status'
        - keep_recent: number of most recently viewed playlists to keep
        """

        if not self.is_history():
            print("No history file found.")
            return

        content = self.load()
        playlists = content.get("playlists", [])

        # Sort playlists by last_viewed descending (most recent first)
        def ts_key(p):
            ts = p.get("last_viewed") or ""
            try:
                return datetime.fromisoformat(ts)
            except Exception:
                return datetime.min

        sorted_playlists = sorted(playlists, key=ts_key, reverse=True)

        # Keep most recent playlists
        keep = sorted_playlists[:keep_recent]
        old = sorted_playlists[keep_recent:]

        for p in old:
            if mode == "playlist":
                # will remove from playlists entirely later
                continue
            elif mode == "videos":
                p["videos"] = []
                p.pop("last_updated", None)
                p.pop("last_viewed", None)
            elif mode == "unwatched":
                p["videos"] = [v for v in p.get("videos", []) if v.get("status")]

        if mode == "playlist":
            # Only keep the most recent
            content["playlists"] = keep
        else:
            # Keep recent + modified old playlists
            content["playlists"] = keep + old

        # Persist
        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(content, f, indent=4)

        print(
            f"History cleared. Mode: {mode}\nKept {keep_recent} most recent playlists."
        )
