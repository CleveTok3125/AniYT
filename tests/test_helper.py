from ani_yt.helper import FormatHelper, LegacyCompatibility


class TestLegacyCompatibility:
    def test_normalize_tuple_list(self):
        inp = [("Title", "https://youtube.com/v")]
        result = LegacyCompatibility.normalize_playlist(inp)
        assert result == [{"video_title": "Title", "video_url": "https://youtube.com/v", "status": ""}]

    def test_normalize_list_of_lists(self):
        inp = [["Title", "https://youtube.com/v"]]
        result = LegacyCompatibility.normalize_playlist(inp)
        assert result == [{"video_title": "Title", "video_url": "https://youtube.com/v", "status": ""}]

    def test_normalize_dict_list(self):
        inp = [{"video_title": "Title", "video_url": "https://youtube.com/v"}]
        result = LegacyCompatibility.normalize_playlist(inp)
        assert result == [{"video_title": "Title", "video_url": "https://youtube.com/v", "status": ""}]

    def test_normalize_dict_with_status(self):
        inp = [{"video_title": "Title", "video_url": "https://youtube.com/v", "status": "viewed"}]
        result = LegacyCompatibility.normalize_playlist(inp)
        assert result[0]["status"] == "viewed"

    def test_normalize_empty(self):
        assert LegacyCompatibility.normalize_playlist([]) == []

    def test_normalize_unsupported(self):
        import pytest

        with pytest.raises(TypeError, match="Unsupported playlist format"):
            LegacyCompatibility.normalize_playlist([123])


class TestFormatHelper:
    def test_beautify_json(self):
        result = FormatHelper.beautify_json({"a": 1, "b": [2]})
        assert "a" in result
        assert "b" in result
