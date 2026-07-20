from ani_yt.input_handler import InputState, OnPressed, ReturnCode


class TestInputState:
    def test_initial(self):
        s = InputState()
        assert s.get_value() == ""
        assert s.buffer == []

    def test_append(self):
        s = InputState()
        s.append("a")
        s.append("b")
        assert s.get_value() == "ab"

    def test_backspace(self):
        s = InputState()
        s.append("a")
        s.append("b")
        s.backspace()
        assert s.get_value() == "a"

    def test_backspace_empty(self):
        s = InputState()
        s.backspace()
        assert s.get_value() == ""

    def test_clear(self):
        s = InputState()
        s.append("abc")
        s.clear()
        assert s.get_value() == ""

    def test_set_str(self):
        s = InputState()
        s.set_str("hello")
        assert s.get_value() == "hello"

    def test_repr(self):
        s = InputState()
        s.append("a")
        r = repr(s)
        assert "buffer" in r
        assert "a" in r


class TestReturnCode:
    def test_valid_codes(self):
        assert ReturnCode.CONTINUE == "CONTINUE"
        assert ReturnCode.BREAK == "BREAK"
        assert ReturnCode.NEXT_PAGE == "NEXT_PAGE"

    def test_contains(self):
        assert "CONTINUE" in ReturnCode
        assert "INVALID" not in ReturnCode

    def test_is_valid(self):
        assert ReturnCode.is_valid("BREAK")
        assert not ReturnCode.is_valid("INVALID")

    def test_invalid_attr(self):
        import pytest

        with pytest.raises(AttributeError):
            _ = ReturnCode.INVALID


class TestOnPressed:
    def test_del_key(self):
        from ani_yt.input_handler import InputHandler

        ih = InputHandler()
        ih.state.set_str("hello")
        result = OnPressed(ih).del_key()
        assert result == "DEL_KEY"
        assert ih.state.get_value() == ""

    def test_enter(self):
        from ani_yt.input_handler import InputHandler

        ih = InputHandler()
        result = OnPressed(ih).enter("\n")
        assert result == "BREAK"

    def test_default(self):
        from ani_yt.input_handler import InputHandler

        ih = InputHandler()
        OnPressed(ih).default("x")
        assert ih.state.get_value() == "x"
