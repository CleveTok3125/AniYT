import os
import shutil
import sys
from typing import List

from wcwidth import wcswidth

from ._internal._display_extension import DisplayExtension
from .common import Typing
from .data_processing import DataProcessing
from .exceptions import PauseableException
from .helper import IOHelper, LegacyCompatibility
from .os_manager import OSManager


class DisplayColor:
    RESET = "\033[0;24;38;2;255;255;255;49m"
    YELLOW = "\033[38;2;255;255;0m"
    LIGHT_GRAY = "\033[0;38;2;187;187;187;49m"
    BRIGHT_BLUE = "\033[38;2;0;191;255m"
    LINK_COLOR = "\033[3;38;2;0;191;255m"
    BOLD = "\033[1m"
    SELECTED_BG_COLOR = "\033[48;5;236m"


class Display_Options:
    def __init__(self, items_per_list=12):
        self.items_per_list = items_per_list
        self.show_opts = False
        self.show_link = False
        self.bookmark = True


class Display:
    @staticmethod
    @IOHelper.gracefully_terminate_exit
    def search():
        return str(input("Search: "))

    @staticmethod
    def clscr():
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")


class DisplayMenu(Display, DisplayExtension):
    def __init__(self, opts: Display_Options, extra_opts={}):
        # Dependencies
        self._init_extra_opts(
            extra_opts
        )  # Some features require additional settings, use it to pass in user settings. Related features should be implemented in DisplayExtension.
        self._inject_dependencies()

        # Variable
        # These values are always created new each time the class is called or are always overwritten.
        self.opts = opts
        self.user_input = ""
        self.data: List[Typing.Video] = []
        self.splited_data = []
        self.len_data = 0
        self.len_last_item = 0
        self.total_items = 0
        self.len_data_items = 0

        # Variable
        # These are variables that are manually cleared for caching purposes. Remember to clear these variables when running functions in the class multiple times.
        self.choosed_item = False

        # Variable
        self._init_loop_values_()

        # Constant
        self.no_opts = {
            "option_toggle": [
                f"{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}(O) Hide all options{DisplayColor.RESET}",
                f"{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}(O) Show all options{DisplayColor.RESET}",
            ],
        }
        self.pages_opts = {
            "N": "(N/→) Next page",
            "P": "(P/←) Previous page",
            "P_int": "(P:<integer>) Jump to page",
            "J": "(J) Jump to next unviewed",
            "U": "(U/↑) Move cursor up",
            "D": "(D/↓) Move cursor down",
            "B_int": "(B:[<integer>]) Add/remove bookmark",
            "T_int": "(T:[<integer>]) View thumbnail",
            "I_int": "(I:<integer>) number of items per page",
            "R": "(R) Re-render the interface",
            "Q": "(Q) Quit",
        }

        # Dynamic
        self._render_dynamic_opts()

    def _render_dynamic_opts(self):
        self.combined_opts = self.pages_opts.copy()

        self.combined_opts["B_toggle"] = (
            f"{DisplayColor.YELLOW if self.bookmark else ''}(B) Toggle bookmark{DisplayColor.RESET}"
        )
        self.combined_opts["L"] = (
            f"{DisplayColor.LINK_COLOR if self.show_link else ''}(L) Toggle link{DisplayColor.RESET}"
        )
        self.combined_opts["O_toggle"] = (
            self.no_opts["option_toggle"][1]
            if not self.opts.show_opts
            else self.no_opts["option_toggle"][0]
        )

        key_order = [
            "O_toggle",
            "N",
            "P",
            "P_int",
            "J",
            "U",
            "D",
            "L",
            "B_toggle",
            "B_int",
            "T_int",
            "I_int",
            "R",
            "Q",
        ]

        self.page_opts_display = "\n".join(
            [self.combined_opts[k] for k in key_order if k in self.combined_opts]
        )

    def _init_loop_values_(self):
        """
        These values are used to process in the while loop.
        Whenever the while loop exits, these values need to be reset if the associated function is to be reused.

        def example(lst):
                index_item = 0
                show_link = False
                bookmark = True
                while index_item < 10:
                        print(lst[index_item] + 'link' if show_link else lst[index_item] + 'bookmark' if bookmark else lst[index_item])

        The values of index_item, show_link and bookmark will always be reset each time the function is called.
        Calling the class every time will not have the problem of instance attributes but will have performance problems.
        """
        self.index_item = 0
        self.cursor_in_page = 0
        self.cursor_moved = False
        self.show_link = self.opts.show_link
        self.bookmark = self.opts.bookmark
        self._last_played = None

    def valid_index_item(self):
        if self.index_item >= self.len_data:
            self.index_item = 0
        elif self.index_item <= -1:
            self.index_item = self.len_data - 1

        if self.splited_data:
            self.cursor_in_page = (
                self.choosed_item - self.index_item * self.opts.items_per_list
            )
            self.cursor_in_page = min(
                self.cursor_in_page, len(self.splited_data[self.index_item]) - 1
            )

    def pagination(self):
        self.valid_index_item()

        self.splited_data = DataProcessing.split_list(
            self.data, self.opts.items_per_list
        )
        self.len_data = len(self.splited_data)

        # Fallback
        if self.len_data == 0:
            self.len_last_item = 0
            self.total_items = 0
            self.splited_data_items = []
            return

        # Validation
        if self.index_item >= self.len_data:
            self.index_item = self.len_data - 1
        elif self.index_item < 0:
            self.index_item = 0

        self.len_last_item = len(self.splited_data[self.len_data - 1])
        self.total_items = (
            self.opts.items_per_list * (self.len_data - 1)
        ) + self.len_last_item
        self.splited_data_items = self.splited_data[self.index_item]

    def print_option(self):
        if self.opts.show_opts:
            output = self.page_opts_display
        else:
            output = self.no_opts["option_toggle"][1]

        print_option_buffer = [output, ""]
        return print_option_buffer

    def print_page_indicator(self):
        showed_item = self.len_data_items + self.index_item * self.opts.items_per_list
        page_colored = (
            f"{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}Page:{DisplayColor.RESET}"
        )
        page_indicator_colored = f"{self.index_item + 1}/{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}{self.len_data}{DisplayColor.RESET}"
        total_item_colored = f"({showed_item}/{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}{self.total_items}{DisplayColor.RESET})"

        print_page_indicator_buffer = [
            f"{page_colored} {page_indicator_colored} {total_item_colored}\n"
        ]
        return print_page_indicator_buffer

    def text_wrap(self, text: str, width: int, indent: int = 0) -> str:
        indent_str = " " * indent
        words = text.split(" ")
        lines = []
        cur_line = ""
        cur_len = 0

        for word in words:
            word_len = wcswidth(word)
            if cur_len + word_len + (1 if cur_line else 0) > width:
                lines.append(cur_line)
                cur_line = word
                cur_len = word_len
            else:
                if cur_line:
                    cur_line += " "
                    cur_len += 1
                cur_line += word
                cur_len += word_len

        if cur_line:
            lines.append(cur_line)

        return ("\n" + indent_str).join(lines)

    def print_menu(self):
        print_menu_buffer = []

        self.len_data_items = len(self.splited_data_items)

        unviewed_indicator = f"{DisplayColor.YELLOW} ❯ {DisplayColor.RESET}"
        cursor_in_page = f"{DisplayColor.BRIGHT_BLUE} ❯ {DisplayColor.RESET}"

        term_width = shutil.get_terminal_size().columns

        for index, item in enumerate(self.splited_data_items):
            item_title = item["video_title"]
            item_url = item["video_url"]

            item_number = self.index_item * self.opts.items_per_list + index + 1

            color_viewed = (
                DisplayColor.LIGHT_GRAY
                if self.history_map.get(item_url, "").lower() == "viewed"
                else ""
            )

            color_bookmarked = (
                DisplayColor.YELLOW
                if getattr(self, "bookmark", True)
                and self.bookmarking_handler.is_bookmarked(item_url)
                else ""
            )

            link_colored = (
                f"\n\t{DisplayColor.LINK_COLOR}{item_url}{DisplayColor.RESET}"
                if self.show_link
                else ""
            )

            indicate_item_len = 3
            indicate_item = " " * indicate_item_len
            is_unviewed_indicator = (
                item_number - 1 == self.choosed_item
                and self.choosed_item is not False
                and not self.cursor_moved
            )
            is_cursor_in_page = index == self.cursor_in_page and self.cursor_moved
            if is_unviewed_indicator:
                indicate_item = unviewed_indicator
            if is_cursor_in_page:
                indicate_item = cursor_in_page

            selected_bg = (
                DisplayColor.SELECTED_BG_COLOR
                if is_cursor_in_page or is_unviewed_indicator
                else ""
            )

            colored_item_number = f"{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}{selected_bg}{color_viewed}{color_bookmarked}{item_number} {DisplayColor.RESET}"
            spaces_num = len(str(self.total_items)) - len(str(item_number))
            spaces_fill = f"{DisplayColor.LIGHT_GRAY}{selected_bg}{"0" * spaces_num}{DisplayColor.RESET}"

            prefix = (
                f"{DisplayColor.RESET}{indicate_item}{spaces_fill}{colored_item_number}"
            )
            visible_prefix_len = (
                indicate_item_len + spaces_num + len(str(item_number)) + 1
            )

            wrapped_item_title = wrapped_item_title = self.text_wrap(
                text=item_title,
                width=term_width - visible_prefix_len - 2,
                indent=visible_prefix_len,
            )
            padding = (term_width - visible_prefix_len - wcswidth(item_title)) * " "
            colored_item = f"{selected_bg}{color_viewed}{color_bookmarked}{wrapped_item_title}{padding}{link_colored}{DisplayColor.RESET}"

            print_menu_buffer.append(f"{prefix}{colored_item}{DisplayColor.RESET}")
        print_menu_buffer.append("")
        return print_menu_buffer

    def print_user_input(self):
        current_index = (
            self.index_item * self.opts.items_per_list + self.cursor_in_page + 1
            if self.splited_data and self.splited_data_items
            else 0
        )

        prompt = (
            f"{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}"
            f"Select ({DisplayColor.YELLOW}{current_index}{DisplayColor.BRIGHT_BLUE}): "
            f"{DisplayColor.RESET}"
        )

        print_user_input_buffer = [prompt]
        return print_user_input_buffer

    def advanced_options(self):
        user_input_upper = self.user_input[:2].upper()
        is_cursor_option = len(self.user_input) == 2

        if len(self.user_input) >= 3 and (user_int := self.user_input[2:]).isdigit():
            user_int = int(user_int)
        elif is_cursor_option:
            if self.cursor_moved:
                user_int = self.cursor_in_page + 1
            else:
                user_int = self.choosed_item + 1
        else:
            return False

        match (user_input_upper, is_cursor_option):
            case ("B:", _):
                self.bookmark_processing(user_int)
            case ("T:", _):
                self.show_thumbnail(user_int)
            case ("P:", False):
                self.index_item = user_int - 1
                self.valid_index_item()
            case ("I:", False):
                self.opts.items_per_list = (
                    user_int
                    if user_int > 0
                    else self.total_items if user_int > self.total_items else 1
                )
                self.pagination()
            case _:
                return False

        return True

    def _handle_enter_input(self):
        # If enter is pressed when the cursor is already on a specific item
        if self.cursor_moved:
            self.choosed_item = (
                self.index_item * self.opts.items_per_list + self.cursor_in_page
            )
            self.cursor_moved = False
        else:
            # If just enter (no auto-play yet) then play correct self.choosed_item
            if self.choosed_item is False:
                self.choosed_item = 0
            else:
                # If user_input is empty multiple times in a row
                # then only increment when the previous set has been played
                if (
                    hasattr(self, "_last_played")
                    and self._last_played == self.choosed_item
                    and any(
                        self.history_map.get(v["video_url"], "").lower() == "viewed"
                        for v in self.data
                    )
                ):
                    if self._last_played != 0:
                        self.choosed_item += 1

    def _handle_numeric_input(self):
        idx = int(self.user_input) - 1
        if idx < 0 or idx >= len(self.data):
            raise IndexError()
        self.choosed_item = idx

    def choose_item_option(self):
        try:
            if self.user_input == "":
                self._handle_enter_input()
            elif self.user_input.isdigit():
                self._handle_numeric_input()
            else:
                raise ValueError()

            ans: Typing.Video = self.data[self.choosed_item]
            # self.mark_viewed(ans["video_url"]) # To avoid hidden actions, should not be used internally in functions should only have display handling functions
            self._last_played = (
                self.choosed_item
            )  # save the episode just played to enter next time auto next

            self.choosed_item = self.find_next_unviewed_index(self.choosed_item + 1)
            self.valid_index_item()
            self.index_item = self.choosed_item // self.opts.items_per_list
            self.cursor_in_page = self.choosed_item % self.opts.items_per_list
            self.cursor_moved = False

            return ans["video_title"], ans["video_url"]

        except ValueError:
            PauseableException(
                "ValueError: only options and non-negative integers are accepted."
            )
        except IndexError:
            PauseableException("IndexError: The requested item is not listed.")
        return

    def standard_options(self):
        user_input = self.user_input.upper()
        handled = True

        match user_input:
            case "O":
                self.opts.show_opts = not self.opts.show_opts
                self._render_dynamic_opts()
            case "N":
                self.index_item += 1
                self.valid_index_item()
                start_idx = self.index_item * self.opts.items_per_list
                self.choosed_item = self.find_next_unviewed_index(start_idx)
                self.cursor_in_page = (
                    self.choosed_item - self.index_item * self.opts.items_per_list
                )
                self.cursor_moved = False
            case "P":
                self.index_item -= 1
                self.valid_index_item()
                start_idx = self.index_item * self.opts.items_per_list
                self.choosed_item = self.find_next_unviewed_index(start_idx)
                self.cursor_in_page = (
                    self.choosed_item - self.index_item * self.opts.items_per_list
                )
                self.cursor_moved = False
            case "J":
                self.choosed_item = self.find_next_unviewed_index(self.choosed_item)
                self.valid_index_item()
                self.index_item = self.choosed_item // self.opts.items_per_list
            case "U":
                if self.cursor_in_page > 0:
                    self.cursor_in_page -= 1
                else:
                    self.cursor_in_page = len(self.splited_data_items) - 1
                self.cursor_moved = True
                self.choosed_item = (
                    self.index_item * self.opts.items_per_list + self.cursor_in_page
                )
            case "D":
                if self.cursor_in_page < len(self.splited_data_items) - 1:
                    self.cursor_in_page += 1
                else:
                    self.cursor_in_page = 0
                self.cursor_moved = True
                self.choosed_item = (
                    self.index_item * self.opts.items_per_list + self.cursor_in_page
                )
            case "L":
                self.show_link = not self.show_link
                self._render_dynamic_opts()
            case "B":
                self.bookmark = not self.bookmark
                self._render_dynamic_opts()
            case "R":
                self._render_dynamic_opts()
            case "Q":
                OSManager.exit(0)
            case _:
                handled = False

        return handled

    def prepare_buffer(self, *args):
        print_buffer_lines = []

        for arg in args:
            if isinstance(arg, (list, tuple)):
                for line in arg:
                    print_buffer_lines.append(str(line))
            else:
                print_buffer_lines.append(str(arg))

        print_buffer = "\n".join(print_buffer_lines)
        return print_buffer

    def choose_menu(self, playlists, clear_choosed_item=False):
        playlists = LegacyCompatibility.normalize_playlist(playlists)

        self.data = playlists
        self.clear_choosed_item = clear_choosed_item
        self.pagination()

        if self.clear_choosed_item or self.choosed_item is False:
            self.choosed_item = self.find_first_unviewed_index()

        self.index_item = self.choosed_item // self.opts.items_per_list

        try:
            while True:
                self.valid_index_item()

                self.splited_data_items = self.splited_data[self.index_item]
                self.len_data_items = len(self.splited_data_items)

                print_option_buffer = self.print_option()
                print_page_indicator_buffer = self.print_page_indicator()
                print_menu_buffer = self.print_menu()
                print_user_input_buffer = self.print_user_input()

                print_buffer = self.prepare_buffer(
                    print_option_buffer,
                    print_page_indicator_buffer,
                    print_menu_buffer,
                    print_user_input_buffer,
                )

                self.clscr()
                print(print_buffer, end="")

                self.get_user_input()

                if self.advanced_options():
                    continue

                if self.standard_options():
                    continue

                if ans := self.choose_item_option():
                    return ans
        finally:
            self._init_loop_values_()
