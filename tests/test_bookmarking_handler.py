import os
from unittest.mock import patch

import pytest

from ani_yt.bookmarking_handler import BookmarkingHandler
from ani_yt.exceptions import CategoryNotExist


class TestBookmarkingHandler:
    @pytest.fixture(autouse=True)
    def setup(self):
        os.makedirs("data", exist_ok=True)

    def test_init_default_data(self):
        bh = BookmarkingHandler()
        data = bh._init_default_data()
        assert "bookmark" in data
        assert "completed" in data

    def test_load_full_data_creates_if_missing(self):
        bh = BookmarkingHandler()
        data = bh.load_full_data()
        assert "bookmark" in data
        assert "completed" in data

    def test_update_item_bookmark(self):
        bh = BookmarkingHandler()
        video = {"video_title": "EP 1", "video_url": "https://youtube.com/1", "status": ""}
        bh.update_item(video, category="bookmark")
        assert bh.is_item_exist("https://youtube.com/1", "bookmark")

    def test_update_item_from_list(self):
        bh = BookmarkingHandler()
        bh.update_item(["EP 1", "https://youtube.com/1"], category="bookmark")
        assert bh.is_item_exist("https://youtube.com/1", "bookmark")

    def test_update_item_new_category(self):
        bh = BookmarkingHandler()
        video = {"video_title": "EP 1", "video_url": "https://youtube.com/1", "status": ""}
        bh.update_item(video, category="favorites", create_new=True)
        assert bh.is_item_exist("https://youtube.com/1", "favorites")

    def test_update_item_missing_category(self):
        bh = BookmarkingHandler()
        video = {"video_title": "EP 1", "video_url": "https://youtube.com/1", "status": ""}
        with patch("ani_yt.input_handler.InputHandler.press_any_key"):
            with pytest.raises(CategoryNotExist):
                bh.update_item(video, category="nonexistent")

    def test_remove_item(self):
        bh = BookmarkingHandler()
        video = {"video_title": "EP 1", "video_url": "https://youtube.com/1", "status": ""}
        bh.update_item(video, category="bookmark")
        bh.remove_item("https://youtube.com/1", "bookmark")
        assert not bh.is_item_exist("https://youtube.com/1", "bookmark")

    def test_remove_nonexistent(self):
        bh = BookmarkingHandler()
        bh.remove_item("https://youtube.com/x", "bookmark")

    def test_get_category(self):
        bh = BookmarkingHandler()
        video = {"video_title": "EP 1", "video_url": "https://youtube.com/1", "status": ""}
        bh.update_item(video, category="bookmark")
        items = bh.get_category("bookmark")
        assert "EP 1" in items
        assert items["EP 1"] == "https://youtube.com/1"

    def test_get_empty_category(self):
        bh = BookmarkingHandler()
        assert bh.get_category("bookmark") == {}

    def test_delete_file(self):
        bh = BookmarkingHandler()
        bh.load_full_data()
        assert os.path.exists(bh.filename)
        bh.delete_file()
        assert not os.path.exists(bh.filename)
