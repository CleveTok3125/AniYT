from typing import NotRequired, TypedDict


class Current(TypedDict):
    video_title: NotRequired[str]
    video_url: NotRequired[str]
    playlist_title: NotRequired[str]
    playlist_url: NotRequired[str]


class Video(TypedDict):
    video_title: str
    video_url: str
    status: str
    last_viewed: NotRequired[str]


class Playlist(TypedDict):
    playlist_title: str
    playlist_url: str
    videos: list[Video]
    last_viewed: NotRequired[str]
    last_updated: NotRequired[str]


class HistoryData(TypedDict):
    current: Current
    playlists: list[Playlist]


class BookmarkData(TypedDict):
    bookmark: dict[str, str]
    completed: dict[str, str]
