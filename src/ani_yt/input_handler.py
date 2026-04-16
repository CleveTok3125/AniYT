from sys import platform, stdout

from .command_history import CommandHistory

if platform.startswith(("linux", "darwin", "freebsd", "openbsd")):
    from .readchar_posix import ReadChar as readchar
elif platform in ("win32", "cygwin"):
    from .readchar_win import ReadChar as readchar
else:
    raise NotImplementedError(f"The platform {platform} is not supported yet")


class InputMap:
    enter = ("\n", "\r", "\r\n")
    backspace = ("\x7f", "\x08")
    arrow_up = ("\x1b[A", "\xe0H", "\x00H")
    arrow_down = ("\x1b[B", "\xe0P", "\x00P")
    arrow_right = ("\x1b[C", "\xe0M", "\x00M")
    arrow_left = ("\x1b[D", "\xe0K", "\x00K")
    del_key = ("\x1b[3~",)
    page_up = ("\x1b[5~", "\xe0I", "\x00I")
    page_down = ("\x1b[6~", "\xe0Q", "\x00Q")


class ReturnCodeMeta(type):
    _valid_codes = {
        "CONTINUE",
        "BREAK",
        "NEXT_PAGE",
        "PREV_PAGE",
        "LINE_UP",
        "LINE_DOWN",
        "DEL_KEY",
        "HISTORY_PREV",
        "HISTORY_NEXT",
    }

    def __getattr__(cls, name):
        if name in cls._valid_codes:
            setattr(cls, name, name)
            return name
        raise AttributeError(f"{name} is not a valid return code")

    def __contains__(cls, item):
        return item in cls._valid_codes

    def is_valid(cls, code):
        return code in {getattr(cls, name) for name in cls._valid_codes}


class ReturnCode(metaclass=ReturnCodeMeta):
    pass


class OnPressed:
    def __init__(self, input_obj):
        self.input_obj = input_obj

    def del_key(self):
        line_len = len(self.input_obj.state.buffer)
        if line_len > 0:
            # print("\b" * line_len + " " * line_len + "\b" * line_len, end="", flush=True)
            self.input_obj.state.clear()
        return ReturnCode.DEL_KEY

    def arrow_left(self, char):
        _ = char
        return ReturnCode.PREV_PAGE

    def arrow_right(self, char):
        _ = char
        return ReturnCode.NEXT_PAGE

    def arrow_up(self, char):
        _ = char
        return ReturnCode.LINE_UP

    def arrow_down(self, char):
        _ = char
        return ReturnCode.LINE_DOWN

    def enter(self, char):
        _ = char
        return ReturnCode.BREAK

    def backspace(self, char):
        _ = char
        if self.input_obj.state.buffer:
            self.input_obj.state.backspace()
            print("\b \b", end="", flush=True)
        return ReturnCode.CONTINUE

    def default(self, char):
        self.input_obj.state.append(char)
        print(char, end="", flush=True)
        return ReturnCode.CONTINUE

    def page_up(self, char):
        _ = char
        return ReturnCode.HISTORY_PREV

    def page_down(self, char):
        _ = char
        return ReturnCode.HISTORY_NEXT


class InputState:
    def __init__(self):
        self.buffer = []

    def clear(self):
        self.buffer.clear()

    def append(self, char: str):
        self.buffer.append(char)

    def backspace(self):
        if self.buffer:
            self.buffer.pop()

    def get_value(self) -> str:
        return "".join(self.buffer)

    def set_str(self, text: str):
        self.buffer = list(text)

    def __repr__(self):
        return f"InputState(buffer={self.buffer!r})"


class InputHandler:
    def __init__(self, command_history_manager: CommandHistory | None = None):
        self.state = InputState()

        self.on_pressed = OnPressed(self)
        self.key_actions = {}
        self.command_history_manager = command_history_manager

        self._config_key_map()

    def _config_key_map(self):
        keymap = (
            "enter",
            "backspace",
            "arrow_left",
            "arrow_right",
            "arrow_up",
            "arrow_down",
            "del_key",
            "page_up",
            "page_down",
        )

        for name in keymap:
            keys = getattr(InputMap, name, None)
            action = getattr(self.on_pressed, name, None)
            if keys and callable(action):
                self._map_keys(keys, action)
            else:
                print(
                    NotImplementedError(
                        f"Key mapping '{name}' is not fully implemented — "
                        f"{'missing InputMap' if keys is None else 'missing OnPressed action'}"
                    )
                )

    def _map_keys(self, keys, action):
        for k in keys:
            self.key_actions[k] = action

    def _redraw_line(self, new_text: str):
        current_len = len(self.state.buffer)

        if current_len > 0:
            print(
                "\b" * current_len + " " * current_len + "\b" * current_len,
                end="",
                flush=True,
            )

        self.state.set_str(new_text)
        print(new_text, end="", flush=True)

    def get_input(self, prompt=None, *, flush_before_read=True, verbose=False):
        self.state.clear()

        stdout.flush()

        if prompt:
            print(prompt, end="", flush=True)

        while True:
            if flush_before_read:
                readchar.flush_input()

            char = readchar.readkey()

            if verbose:
                print(f"[DEBUG] char={repr(char)}, buffer={self.state.buffer}")

            action = self.key_actions.get(char, self.on_pressed.default)
            code = action(char)

            if self.command_history_manager:
                if code == ReturnCode.HISTORY_PREV:
                    prev_cmd = self.command_history_manager.backward()
                    if prev_cmd is not None:
                        self._redraw_line(prev_cmd)
                    continue

                if code == ReturnCode.HISTORY_NEXT:
                    next_cmd = self.command_history_manager.forward()
                    self._redraw_line(next_cmd)
                    continue

            if code == ReturnCode.BREAK:
                print()
                break

            if code == ReturnCode.CONTINUE:
                continue

            return code

        user_input = self.state.get_value()

        if self.command_history_manager:
            self.command_history_manager.add_command(user_input)

        return user_input

    @staticmethod
    def press_any_key(prompt=None):
        if prompt is None:
            prompt = "Press any key to continue..."

        stdout.flush()

        if prompt is not False:
            print(prompt, end="", flush=True)

        result = bool(readchar.readchar())

        print()

        return result
