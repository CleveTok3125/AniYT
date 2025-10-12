class DisplayColor:
    RESET = "\033[0;24;38;2;255;255;255;49m"
    YELLOW = "\033[38;2;255;255;0m"
    LIGHT_GRAY = "\033[0;38;2;187;187;187;49m"
    BRIGHT_BLUE = "\033[38;2;0;191;255m"
    GREEN = "\033[38;2;0;128;0;49m"
    LINK_COLOR = "\033[3;38;2;0;191;255m"
    BOLD = "\033[1m"
    SELECTED_BG_COLOR = "\033[48;5;236m"
    ALT_BG_1 = ""
    ALT_BG_2 = "\033[48;5;236m"
    BLOCK = "███"
    CONTINUATION_SYMBOL = "↳ "

    COLOR_MAP = {
        YELLOW: "Bookmarked",
        LIGHT_GRAY: "Viewed",
        GREEN: "Completed",
    }
