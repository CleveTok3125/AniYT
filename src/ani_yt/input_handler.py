import readchar


class InputMap:
    enter = ("\n", "\r")
    backspace = "\x7f"
    arrow_up = "\x1b[A"
    arrow_down = "\x1b[B"
    arrow_right = "\x1b[C"
    arrow_left = "\x1b[D"


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
        self.key_actions = {
            **{k: self.on_pressed.enter for k in InputMap.enter},
            InputMap.backspace: self.on_pressed.backspace,
            InputMap.arrow_left: self.on_pressed.arrow_left,
            InputMap.arrow_right: self.on_pressed.arrow_right,
            InputMap.arrow_up: self.on_pressed.arrow_up,
            InputMap.arrow_down: self.on_pressed.arrow_down,
        }

    def get_input(self, prompt=None, verbose=False):
        print(prompt, end="", flush=True)

        while True:
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
