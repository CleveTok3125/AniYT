from ani_yt.player import PlayerConfig, TermuxPlayerConfig


class TestPlayerConfig:
    def test_get_default_mpv_args(self):
        args = PlayerConfig.get("mpv_args")
        assert isinstance(args, list)
        assert len(args) > 0

    def test_update_mpv_args(self):
        PlayerConfig.update(mpv_args=["--test"])
        assert PlayerConfig.get("mpv_args") == ["--test"]

    def test_update_unknown_key(self):
        import pytest

        with pytest.raises(KeyError):
            PlayerConfig.update(unknown_key="value")

    def test_get_nonexistent_key(self):
        assert PlayerConfig.get("nonexistent") is None

    def test_get_all_settings(self):
        settings = PlayerConfig.get_all_settings()
        assert isinstance(settings, dict)
        assert "mpv_args" in settings


class TestTermuxPlayerConfig:
    def test_inherits_base(self):
        assert TermuxPlayerConfig.get("mpv_args") is not None

    def test_termux_specific_keys(self):
        assert isinstance(TermuxPlayerConfig.get("monitor"), int)
        assert isinstance(TermuxPlayerConfig.get("open_app"), bool)
        assert isinstance(TermuxPlayerConfig.get("return_app"), bool)
        assert isinstance(TermuxPlayerConfig.get("mpv_fullscreen_playback"), bool)
        assert isinstance(TermuxPlayerConfig.get("touch_mouse_gestures"), bool)

    def test_get_all_settings(self):
        settings = TermuxPlayerConfig.get_all_settings()
        assert "monitor" in settings
        assert "open_app" in settings
