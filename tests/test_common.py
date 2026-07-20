from ani_yt.common import BookmarkData, Current, HistoryData, Playlist, Video


class TestVideo:
    def test_minimal(self):
        v: Video = {"video_title": "EP 1", "video_url": "https://youtube.com/1", "status": ""}
        assert v["video_title"] == "EP 1"
        assert v["video_url"] == "https://youtube.com/1"
        assert v["status"] == ""

    def test_with_last_viewed(self):
        v: Video = {
            "video_title": "EP 2",
            "video_url": "https://youtube.com/2",
            "status": "viewed",
            "last_viewed": "2024-01-01T12:00:00",
        }
        assert v["last_viewed"] == "2024-01-01T12:00:00"


class TestCurrent:
    def test_empty(self):
        c: Current = {}
        assert len(c) == 0

    def test_full(self):
        c: Current = {
            "video_title": "EP 1",
            "video_url": "https://youtube.com/1",
            "playlist_title": "My Playlist",
            "playlist_url": "https://youtube.com/playlist?list=ABC",
        }
        assert c["playlist_url"] == "https://youtube.com/playlist?list=ABC"


class TestPlaylist:
    def test_minimal(self):
        p: Playlist = {"playlist_title": "P", "playlist_url": "https://youtube.com/p", "videos": []}
        assert p["videos"] == []

    def test_with_videos(self):
        p: Playlist = {
            "playlist_title": "P",
            "playlist_url": "https://youtube.com/p",
            "videos": [{"video_title": "E1", "video_url": "https://youtube.com/1", "status": ""}],
        }
        assert len(p["videos"]) == 1

    def test_with_timestamps(self):
        p: Playlist = {
            "playlist_title": "P",
            "playlist_url": "https://youtube.com/p",
            "videos": [],
            "last_viewed": "2024-06-15T10:00:00",
            "last_updated": "2024-06-15T10:00:00",
        }
        assert isinstance(p["last_viewed"], str)
        assert isinstance(p["last_updated"], str)


class TestHistoryData:
    def test_default(self):
        h: HistoryData = {"current": {}, "playlists": []}
        assert h["current"] == {}
        assert h["playlists"] == []


class TestBookmarkData:
    def test_default(self):
        b: BookmarkData = {"bookmark": {}, "completed": {}}
        assert "bookmark" in b
        assert "completed" in b

    def test_with_items(self):
        b: BookmarkData = {
            "bookmark": {"EP 1": "https://youtube.com/1"},
            "completed": {"EP 2": "https://youtube.com/2"},
        }
        assert b["bookmark"]["EP 1"] == "https://youtube.com/1"
