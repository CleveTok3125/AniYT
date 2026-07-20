from unittest.mock import patch

import pytest

from ani_yt.main import Main


class TestMain:
    def test_init_defaults(self):
        m = Main(channel_url="")
        assert m.channel_url == ""
        assert m.opts == "auto"

    def test_init_with_channel(self):
        m = Main(channel_url="https://youtube.com/@ch", opts="android")
        assert m.channel_url == "https://youtube.com/@ch"
        assert m.opts == "android"

    def test_update_multiple_public_method(self):
        m = Main(channel_url="")
        assert hasattr(m, "update_multiple")

    def test_source_template(self):
        m = Main(channel_url="")
        m.source_template()

    def test_clear_cache(self):
        m = Main(channel_url="")
        m.clear_cache()

    def test_delete_history(self):
        m = Main(channel_url="")
        m.delete_history()

    def test_delete_bookmark(self):
        m = Main(channel_url="")
        m.delete_bookmark()

    @patch("ani_yt.main.YT_DLP")
    def test_update_calls_omit(self, mock_ytdlp):
        m = Main(channel_url="https://youtube.com/@ch")
        mock_ytdlp.return_value.get_playlist.return_value = {
            "entries": [{"_type": "url", "title": "V1", "url": "https://youtube.com/v1"}]
        }
        m.update()

    def test_search_empty_query(self):
        m = Main(channel_url="")
        with pytest.raises(SystemExit):
            m.search("")

    def test_menu_empty(self):
        m = Main(channel_url="")
        m.menu([])

    def test_playlist_from_url_no_videos(self):
        m = Main(channel_url="")
        data = {"entries": []}

        class FakeDLP:
            @staticmethod
            def get_video(url):
                return data

        m.dlp = FakeDLP()
        m.playlist_from_url("https://youtube.com/p")
