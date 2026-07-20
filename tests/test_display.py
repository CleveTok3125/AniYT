from ani_yt.display import BACK_SENTINEL, Display_Options


class TestDisplayOptions:
    def test_default_values(self):
        opts = Display_Options()
        assert opts.items_per_list == 12
        assert opts.show_opts is False
        assert opts.show_link is False
        assert opts.bookmark is True

    def test_custom_items_per_list(self):
        opts = Display_Options(items_per_list=20)
        assert opts.items_per_list == 20


class TestBackSentinel:
    def test_back_sentinel(self):
        assert BACK_SENTINEL == ("__BACK__", "")

    def test_back_sentinel_unpack(self):
        title, url = BACK_SENTINEL
        assert title == "__BACK__"
        assert url == ""
