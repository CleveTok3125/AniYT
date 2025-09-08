from typing import Dict, List

import ujson as json

from .exceptions import InvalidHistoryFile
from .os_manager import OSManager

Video = Dict[str, str]
VideoData = List[Video]
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

    def update(self, curr: Dict = None, playlists: List[Playlist] = None):
        is_history = self.is_history()
        if is_history:
            content = self.load()
        else:
            content = {"current": {}, "playlists": []}

        # Update current video
        if curr:
            content["current"] = curr

        # Update playlists
        if playlists:
            content["playlists"] = playlists

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
