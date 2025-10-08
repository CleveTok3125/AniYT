from sys import platform

if platform.startswith(("linux", "darwin", "freebsd", "openbsd")):
    from .readchar_posix import ReadChar as readchar
elif platform in ("win32", "cygwin"):
    from .readchar_win import ReadChar as readchar
else:
    raise NotImplementedError(f"The platform {platform} is not supported yet")


class InputMap:
    enter = ("\n", "\r", "\r\n")
    backspace = ("\x7f", "\x08")
    arrow_up = ("\x1b[A", "\xe0H")
    arrow_down = ("\x1b[B", "\xe0P")
    arrow_right = ("\x1b[C", "\xe0M")
    arrow_left = ("\x1b[D", "\xe0K")


class ReturnCodeMeta(type):
    _valid_codes = {
        "CONTINUE",
        "BREAK",
        "NEXT_PAGE",
        "PREV_PAGE",
        "LINE_UP",
        "LINE_DOWN",
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

    def arrow_left(self, char):
        return ReturnCode.PREV_PAGE

    def arrow_right(self, char):
        return ReturnCode.NEXT_PAGE

    def arrow_up(self, char):
        return ReturnCode.LINE_UP

    def arrow_down(self, char):
        return ReturnCode.LINE_DOWN

    def enter(self, char):
        return ReturnCode.BREAK

    def backspace(self, char):
        if self.input_obj.input_chars:
            self.input_obj.input_chars.pop()
            print("\b \b", end="", flush=True)
        return ReturnCode.CONTINUE

    def default(self, char):
        self.input_obj.input_chars.append(char)
        print(char, end="", flush=True)
        return ReturnCode.CONTINUE


class InputHandler:
    def __init__(self):
        self.input_chars = []
        self.on_pressed = OnPressed(self)
        self.key_actions = {}

        self._map_keys(InputMap.enter, self.on_pressed.enter)
        self._map_keys(InputMap.backspace, self.on_pressed.backspace)
        self._map_keys(InputMap.arrow_left, self.on_pressed.arrow_left)
        self._map_keys(InputMap.arrow_right, self.on_pressed.arrow_right)
        self._map_keys(InputMap.arrow_up, self.on_pressed.arrow_up)
        self._map_keys(InputMap.arrow_down, self.on_pressed.arrow_down)

    def _map_keys(self, keys, action):
        for k in keys:
            if isinstance(k, (tuple, list)):
                for subk in k:
                    self.key_actions[subk] = action
            else:
                self.key_actions[k] = action

    def get_input(self, prompt=None, *, flush_before_read=True, verbose=False):
        print(prompt, end="", flush=True)

        while True:
            if flush_before_read:
                readchar.flush_input()

            char = readchar.readkey()

            if verbose:
                print(repr(char))

            action = self.key_actions.get(char, self.on_pressed.default)
            code = action(char)

            if code == ReturnCode.BREAK:
                print()
                break

            if code == ReturnCode.CONTINUE:
                continue

            return code

        return "".join(self.input_chars)
