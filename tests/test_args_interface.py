from unittest.mock import MagicMock, patch

import pytest

from ani_yt.args_interface import ArgsHandler


class TestArgsHandler:
    def test_init_with_version(self):
        with patch("sys.argv", ["ani-yt", "--version"]):
            with patch.object(ArgsHandler, "print_version") as mock_version:
                ArgsHandler()
                mock_version.assert_called()

    def test_init_no_args_prints_help(self):
        with patch("sys.argv", ["ani-yt"]):
            with patch("ani_yt.args_interface.ArgsHandler._args_wrapping"):
                with patch("ani_yt.args_interface.ArgsHandler._argument_preprocessing"):
                    handler = ArgsHandler()
                    assert handler.parser is not None

    def test_run_main_valid_action(self):
        with patch("sys.argv", ["ani-yt"]):
            with patch("ani_yt.args_interface.ArgsHandler._args_wrapping"):
                with patch("ani_yt.args_interface.ArgsHandler._argument_preprocessing"):
                    handler = ArgsHandler()
                    handler.actions = {"clear_cache": MagicMock()}
                    handler.main = MagicMock()
                    result = handler.run_main("clear_cache")
                    handler.actions["clear_cache"].assert_called_once()

    def test_listener_no_args(self):
        with patch("sys.argv", ["ani-yt"]):
            with patch("ani_yt.args_interface.ArgsHandler._args_wrapping"):
                with patch("ani_yt.args_interface.ArgsHandler._argument_preprocessing"):
                    handler = ArgsHandler()
                    handler.actions = {}
                    with patch.object(handler.parser, "print_help") as mock_help:
                        with pytest.raises(SystemExit):
                            handler.listener()
                        mock_help.assert_called_once()
