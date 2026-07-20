from ani_yt.exceptions import MissingChannelUrl


class TestMissingChannelUrl:
    def test_is_exception(self):
        assert issubclass(MissingChannelUrl, Exception)

    def test_raise(self):
        import pytest

        with pytest.raises(MissingChannelUrl):
            raise MissingChannelUrl("test")
