from datetime import datetime
from typing import Dict, List, NotRequired, TypedDict


class Current(TypedDict):
    video_title: NotRequired[str]
    video_url: NotRequired[str]
    playlist_title: NotRequired[str]
    playlist_url: NotRequired[str]


class Video(TypedDict):
    video_title: str
    video_url: str
    status: str
    last_viewed: NotRequired[datetime]


class Playlist(TypedDict):
    playlist_title: str
    playlist_url: str
    videos: List[Video]
    last_viewed: NotRequired[datetime]
    last_updated: NotRequired[datetime]


class HistoryData(TypedDict):
    current: Current
    playlists: List[Playlist]


class BookmarkData(TypedDict):
    bookmark: Dict[str, str]
    completed: Dict[str, str]
