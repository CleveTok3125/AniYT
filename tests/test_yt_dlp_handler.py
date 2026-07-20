from unittest.mock import patch

import pytest

from ani_yt.yt_dlp_handler import YT_DLP, YT_DLP_Options


class TestYTDLPOptions:
    def test_default_opts(self):
        opts = YT_DLP_Options()
        assert opts.ydl_opts["extract_flat"] is True
        assert opts.ydl_opts["quiet"] is True

    def test_custom_opts(self):
        opts = YT_DLP_Options(quiet=False, no_warnings=False)
        assert opts.ydl_opts["quiet"] is False
        assert opts.ydl_opts["no_warnings"] is False


class TestYTDLP:
    def test_init_no_url(self):
        dlp = YT_DLP(None, YT_DLP_Options())
        assert dlp.channel_url is None

    def test_init_with_url(self):
        dlp = YT_DLP("https://youtube.com/@channel", YT_DLP_Options())
        assert dlp.channel_url is not None

    def test_parse_channel_url_id(self):
        dlp = YT_DLP("UC_test123", YT_DLP_Options())
        assert "UC_test123" in dlp.channel_url

    @patch("ani_yt.yt_dlp_handler.YT_DLP.standalone_get_video")
    def test_get_video_calls_standalone(self, mock_get_video):
        mock_get_video.return_value = {"entries": []}
        dlp = YT_DLP("https://youtube.com/@ch", YT_DLP_Options())
        result = dlp.get_video("https://youtube.com/p")
        mock_get_video.assert_called_once()
        assert result == {"entries": []}

    @patch("ani_yt.yt_dlp_handler.YT_DLP.standalone_get_video")
    def test_standalone_get_thumbnail_success(self, mock_get_video):
        mock_get_video.return_value = {
            "thumbnails": [{"url": "https://img.youtube.com/1.jpg"}, {"url": "https://img.youtube.com/2.jpg"}]
        }
        url = YT_DLP.standalone_get_thumbnail("https://youtube.com/v", {})
        assert url == "https://img.youtube.com/2.jpg"

    @patch("ani_yt.yt_dlp_handler.YT_DLP.standalone_get_video")
    def test_standalone_get_thumbnail_none(self, mock_get_video):
        mock_get_video.return_value = None
        url = YT_DLP.standalone_get_thumbnail("https://youtube.com/v", {})
        assert url == ""

    @patch("ani_yt.yt_dlp_handler.YT_DLP.get_video")
    def test_get_stream_success(self, mock_get_video):
        mock_get_video.return_value = {
            "requested_formats": [
                {"url": "https://stream1.com/video"},
                {"url": "https://stream2.com/audio"},
            ]
        }
        dlp = YT_DLP("https://youtube.com/@ch", YT_DLP_Options())
        v_url, a_url = dlp.get_stream("https://youtube.com/v")
        assert v_url == "https://stream1.com/video"
        assert a_url == "https://stream2.com/audio"

    @patch("ani_yt.yt_dlp_handler.YT_DLP.get_video")
    def test_get_stream_none(self, mock_get_video):
        mock_get_video.return_value = None
        dlp = YT_DLP("https://youtube.com/@ch", YT_DLP_Options())
        v_url, a_url = dlp.get_stream("https://youtube.com/v")
        assert v_url == ""
        assert a_url == ""

    @patch("subprocess.run")
    def test_download_success(self, mock_run):
        mock_run.return_value.stdout = b"/path/to/video.mp4"
        result = YT_DLP.download("https://youtube.com/v", "all", capture_output=True)
        assert result == b"/path/to/video.mp4"
        mock_run.assert_called_once()
