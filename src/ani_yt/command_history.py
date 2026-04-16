from collections import deque


class CommandHistory:
    def __init__(self, max_size=100):
        self.__history = deque(maxlen=max_size)
        self.__index = -1

    def add_command(self, command, dedup=True):
        clean_command = command.strip()
        if not clean_command:
            return

        if self.__history and dedup and self.__history[-1] == clean_command:
            return

        self.__history.append(clean_command)
        self.__index = -1

    def backward(self):
        if not self.__history:
            return

        if self.__index == -1:
            self.__index = len(self.__history) - 1
        elif self.__index > 0:
            self.__index -= 1

        return self.__history[self.__index]

    def forward(self):
        if self.__index == -1 or not self.__history:
            return ""

        if self.__index < len(self.__history) - 1:
            self.__index += 1
            return self.__history[self.__index]
        else:
            self.__index = -1
            return ""

    def current(self):
        return self.__history[self.__index]

    def print_history(self):
        for i, command in enumerate(self.__history, 1):
            print(f"{i}. {command}")
