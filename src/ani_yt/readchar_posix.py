# Forked from https://github.com/magmax/python-readchar

import os
import sys
import termios


class ReadChar:
    INTERRUPT_KEYS = ("\x03",)

    @staticmethod
    def readchar() -> str:
        """Reads a single character from the input stream.
        Blocks until a character is available."""

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        term = termios.tcgetattr(fd)
        try:
            term[3] &= ~(
                termios.ICANON | termios.ECHO | termios.IGNBRK | termios.BRKINT
            )
            termios.tcsetattr(fd, termios.TCSAFLUSH, term)

            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    @staticmethod
    def readkey() -> str:
        """Get a keypress. If an escaped key is pressed, the full sequence is
        read and returned as noted in `_posix_key.py`."""

        c1 = ReadChar.readchar()

        if c1 in ReadChar.INTERRUPT_KEYS:
            raise KeyboardInterrupt

        if c1 != "\x1b":
            return c1

        c2 = ReadChar.readchar()
        if c2 not in "\x4f\x5b":
            return c1 + c2

        c3 = ReadChar.readchar()
        if c3 not in "\x31\x32\x33\x35\x36":
            return c1 + c2 + c3

        c4 = ReadChar.readchar()
        if c4 not in "\x30\x31\x33\x34\x35\x37\x38\x39":
            return c1 + c2 + c3 + c4

        c5 = ReadChar.readchar()
        return c1 + c2 + c3 + c4 + c5

    @staticmethod
    def flush_input():
        fd = sys.stdin.fileno()
        if os.isatty(fd):
            termios.tcflush(fd, termios.TCIFLUSH)
