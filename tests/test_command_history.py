from ani_yt.command_history import CommandHistory


class TestCommandHistory:
    def test_empty(self):
        ch = CommandHistory()
        assert ch.backward() is None
        assert ch.forward() == ""

    def test_add_and_backward(self):
        ch = CommandHistory()
        ch.add_command("cmd1")
        ch.add_command("cmd2")
        assert ch.backward() == "cmd2"
        assert ch.backward() == "cmd1"
        assert ch.backward() == "cmd1"

    def test_forward(self):
        ch = CommandHistory()
        ch.add_command("cmd1")
        ch.add_command("cmd2")
        ch.backward()
        ch.backward()
        assert ch.forward() == "cmd2"
        assert ch.forward() == ""

    def test_multiple_add_same(self):
        ch = CommandHistory()
        ch.add_command("cmd1")
        ch.add_command("cmd1")
        ch.backward()
        assert ch.backward() == "cmd1"
