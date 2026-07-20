import os

import pytest

from ani_yt.history_handler import HistoryHandler


class TestHistoryHandler:
    def _make_handler(self):
        return HistoryHandler()

    def test_is_history_default(self):
        assert not self._make_handler().is_history()

    def test_load_nonexistent_raises(self):
        with pytest.raises(SystemExit):
            self._make_handler().load()

    def test_update_creates_file(self):
        h = self._make_handler()
        h.update(curr={"playlist_url": "https://youtube.com/p"})
        assert h.is_history()

    def test_update_and_load(self):
        h = self._make_handler()
        h.update(curr={"playlist_title": "P", "playlist_url": "https://youtube.com/p"})
        data = h.load()
        assert data["current"]["playlist_url"] == "https://youtube.com/p"

    def test_update_with_videos(self):
        h = self._make_handler()
        videos = [{"video_title": "E1", "video_url": "https://youtube.com/1", "status": ""}]
        h.update(
            curr={"playlist_title": "P", "playlist_url": "https://youtube.com/p"},
            videos=videos,
        )
        data = h.load()
        playlist = data["playlists"][0]
        assert len(playlist["videos"]) == 1
        assert "last_updated" in playlist

    def test_update_with_viewed(self):
        h = self._make_handler()
        h.update(curr={"playlist_url": "https://youtube.com/p"}, viewed=True)
        data = h.load()
        playlist = data["playlists"][0]
        assert "last_viewed" in playlist

    def test_update_merge_videos(self):
        h = self._make_handler()
        v1 = [{"video_title": "E1", "video_url": "https://youtube.com/1", "status": ""}]
        h.update(curr={"playlist_url": "https://youtube.com/p"}, videos=v1, truncate=False)

        v2 = [{"video_title": "E2", "video_url": "https://youtube.com/2", "status": ""}]
        h.update(curr={"playlist_url": "https://youtube.com/p"}, videos=v2, truncate=False)

        data = h.load()
        assert len(data["playlists"][0]["videos"]) == 2

    def test_replace_playlists(self):
        h = self._make_handler()
        playlists = [
            {"playlist_title": "P1", "playlist_url": "https://youtube.com/p1", "videos": []},
        ]
        h.update(playlists=playlists)
        data = h.load()
        assert len(data["playlists"]) == 1
        assert data["playlists"][0]["playlist_title"] == "P1"

    def test_search_existing(self):
        h = self._make_handler()
        history = {
            "current": {},
            "playlists": [
                {
                    "playlist_title": "P",
                    "playlist_url": "https://youtube.com/p",
                    "videos": [
                        {"video_title": "E1", "video_url": "https://youtube.com/1", "status": ""},
                        {"video_title": "E2", "video_url": "https://youtube.com/2", "status": ""},
                    ],
                }
            ],
        }
        p_idx, v_idx = h.search("https://youtube.com/2", history)
        assert p_idx == 0
        assert v_idx == 1

    def test_search_not_found(self):
        h = self._make_handler()
        history = {"current": {}, "playlists": []}
        p_idx, v_idx = h.search("https://youtube.com/x", history)
        assert p_idx == -1
        assert v_idx == -1

    def test_clear_history_playlist_mode(self):
        h = self._make_handler()
        h.update(curr={"playlist_url": "https://youtube.com/p1"}, viewed=True)
        h.clear_history(mode="playlist", keep_recent=1)
        data = h.load()
        assert len(data["playlists"]) == 1

    def test_clear_history_videos_mode(self):
        h = self._make_handler()
        v1 = [{"video_title": "E1", "video_url": "https://youtube.com/1", "status": ""}]
        h.update(curr={"playlist_url": "https://youtube.com/p1"}, videos=v1, viewed=True)
        v2 = [{"video_title": "E2", "video_url": "https://youtube.com/2", "status": ""}]
        h.update(curr={"playlist_url": "https://youtube.com/p2"}, videos=v2, viewed=True)
        h.clear_history(mode="videos", keep_recent=1)
        data = h.load()
        assert len(data["playlists"]) == 2
        kept = [p for p in data["playlists"] if p["playlist_url"] == "https://youtube.com/p2"]
        cleared = [p for p in data["playlists"] if p["playlist_url"] == "https://youtube.com/p1"]
        assert len(kept[0]["videos"]) == 1
        assert cleared[0]["videos"] == []

    def test_delete_history(self):
        h = self._make_handler()
        h.update(curr={"playlist_url": "https://youtube.com/p"})
        assert h.is_history()
        h.delete_history()
        assert not h.is_history()
