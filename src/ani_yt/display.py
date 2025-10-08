import os
import shutil
import sys
from datetime import datetime
from typing import Dict, List

from wcwidth import wcswidth

from .bookmarking_handler import BookmarkingHandler
from .data_processing import DataProcessing
from .exceptions import PauseableException
from .helper import IOHelper, LegacyCompatibility
from .history_handler import HistoryHandler
from .input_handler import InputHandler, ReturnCode
from .os_manager import OSManager
from .player import Player
from .yt_dlp_handler import YT_DLP, YT_DLP_Options

Video = Dict[str, str]


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


class DisplayExtension:
    def _inject_dependencies(
        self,
    ):  # Only used when you want to declare an instance, other values ​​like str, int, list, etc can be taken directly from extra_opts
        self.bookmarking_handler = self._get_dependencies(
            "bookmark",
            BookmarkingHandler,
        )

        self.yt_dlp_opts = self._get_dependencies(
            "yt-dlp",
            YT_DLP_Options,
        )

    def _init_extra_opts(self, extra_opts):
        self.extra_opts = extra_opts

        if not isinstance(extra_opts, dict):
            raise TypeError(
                f"The parameter passed should be a dictionary, but got {type(extra_opts)}"
            )

    def _get_dependencies(
        self, requirement: object, requirement_suggestion: type, fallback_factory=None
    ):
        dependency = self.extra_opts.get(requirement)

        if dependency is None:
            raise ValueError(f"Missing required dependency: {requirement}")
        if not isinstance(dependency, requirement_suggestion):
            raise TypeError(
                f"Dependency '{requirement}' must be an instance of {requirement_suggestion}"
            )

        return dependency

    def bookmark_processing(self, user_int):
        try:
            item: Video = self.data[user_int - 1]
            if self.bookmarking_handler.is_bookmarked(item["video_url"]):
                self.bookmarking_handler.remove_bookmark(item["video_url"])
            else:
                self.bookmarking_handler.update(item)
        except ValueError:
            PauseableException("ValueError: only non-negative integers are accepted.")
        except IndexError:
            PauseableException("IndexError: The requested item is not listed.")

    def open_image_with_mpv(self, url):
        Player.start_with_mode(url=url, opts=self.extra_opts.get("mode", "auto"))

    def show_thumbnail(self, user_int):
        item: Video = self.data[user_int - 1]
        url = item["video_url"]

        thumbnail_url = YT_DLP.standalone_get_thumbnail(url, self.yt_dlp_opts.ydl_opts)
        self.open_image_with_mpv(thumbnail_url)


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
        self.data: List[Video] = []
        self.splited_data = []
        self.len_data = 0
        self.len_last_item = 0
        self.total_items = 0
        self.len_data_items = 0

        # Variable
        # These are variables that are manually cleared for caching purposes. Remember to clear these variables when running functions in the class multiple times.
        self.choosed_item = False

        # Constant
        self.RESET = "\033[0;24;38;2;255;255;255;49m"
        self.YELLOW = "\033[38;2;255;255;0m"
        self.LIGHT_GRAY = "\033[0;38;2;187;187;187;49m"
        self.BRIGHT_BLUE = "\033[38;2;0;191;255m"
        self.LINK_COLOR = "\033[3;38;2;0;191;255m"
        self.BOLD = "\033[1m"
        self.SELECTED_BG_COLOR = "\033[48;5;236m"

        # Variable
        self._init_loop_values_()

        # Constant
        self.no_opts = {
            "option_toggle": [
                f"{self.BRIGHT_BLUE}{self.BOLD}(O) Hide all options{self.RESET}",
                f"{self.BRIGHT_BLUE}{self.BOLD}(O) Show all options{self.RESET}",
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

        # History handler
        self.history_handler = HistoryHandler()
        self.history_map = {}
        if self.history_handler and self.history_handler.is_history():
            try:
                history = self.history_handler.load()
                # Build video_url -> status map
                self.history_map = {
                    video["video_url"]: video.get("status", "")
                    for playlist in history.get("playlists", [])
                    for video in playlist.get("videos", [])
                }
            except Exception:
                self.history_map = {}

    def _find_first_unviewed_index(self):
        if not hasattr(self, "data") or not self.data:
            return 0

        for idx, video in enumerate(self.data):
            if self.history_map.get(video["video_url"], "").lower() != "viewed":
                return idx
        return 0

    def _find_next_unviewed_index(self, start_idx=0):
        if not self.data:
            return 0
        for idx in range(start_idx, len(self.data)):
            if (
                self.history_map.get(self.data[idx]["video_url"], "").lower()
                != "viewed"
            ):
                return idx

        for idx in range(0, start_idx):
            if (
                self.history_map.get(self.data[idx]["video_url"], "").lower()
                != "viewed"
            ):
                return idx
        return 0

    def _render_dynamic_opts(self):
        self.combined_opts = self.pages_opts.copy()

        self.combined_opts["B_toggle"] = (
            f"{self.YELLOW if self.bookmark else ''}(B) Toggle bookmark{self.RESET}"
        )
        self.combined_opts["L"] = (
            f"{self.LINK_COLOR if self.show_link else ''}(L) Toggle link{self.RESET}"
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

    def mark_viewed(self, url: str):
        """
        Mark the video as viewed in both history file and local map, and update last_viewed timestamp.
        """
        history = self.history_handler.load()

        p_idx, v_idx = self.history_handler.search(url, history)
        if p_idx != -1 and v_idx != -1:
            history["playlists"][p_idx]["videos"][v_idx]["status"] = "viewed"

            now = datetime.now().astimezone().isoformat()
            history["playlists"][p_idx]["videos"][v_idx]["last_viewed"] = now

            # persist
            self.history_handler.update(
                curr=history.get("current"), playlists=history.get("playlists")
            )
            # update local map
            self.history_map[url] = "viewed"

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
        page_colored = f"{self.BRIGHT_BLUE}{self.BOLD}Page:{self.RESET}"
        page_indicator_colored = f"{self.index_item + 1}/{self.BRIGHT_BLUE}{self.BOLD}{self.len_data}{self.RESET}"
        total_item_colored = f"({showed_item}/{self.BRIGHT_BLUE}{self.BOLD}{self.total_items}{self.RESET})"

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

        unviewed_indicator = f"{self.YELLOW} ❯ {self.RESET}"
        cursor_in_page = f"{self.BRIGHT_BLUE} ❯ {self.RESET}"

        term_width = shutil.get_terminal_size().columns

        for index, item in enumerate(self.splited_data_items):
            item_title = item["video_title"]
            item_url = item["video_url"]

            item_number = self.index_item * self.opts.items_per_list + index + 1

            color_viewed = (
                self.LIGHT_GRAY
                if self.history_map.get(item_url, "").lower() == "viewed"
                else ""
            )

            color_bookmarked = (
                self.YELLOW
                if getattr(self, "bookmark", True)
                and self.bookmarking_handler.is_bookmarked(item_url)
                else ""
            )

            link_colored = (
                f"\n\t{self.LINK_COLOR}{item_url}{self.RESET}" if self.show_link else ""
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
                self.SELECTED_BG_COLOR
                if is_cursor_in_page or is_unviewed_indicator
                else ""
            )

            colored_item_number = f"{self.BRIGHT_BLUE}{self.BOLD}{selected_bg}{color_viewed}{color_bookmarked}{item_number} {self.RESET}"
            spaces_num = len(str(self.total_items)) - len(str(item_number))
            spaces_fill = (
                f"{self.LIGHT_GRAY}{selected_bg}{"0" * spaces_num}{self.RESET}"
            )

            prefix = f"{self.RESET}{indicate_item}{spaces_fill}{colored_item_number}"
            visible_prefix_len = (
                indicate_item_len + spaces_num + len(str(item_number)) + 1
            )

            wrapped_item_title = wrapped_item_title = self.text_wrap(
                text=item_title,
                width=term_width - visible_prefix_len - 2,
                indent=visible_prefix_len,
            )
            padding = (term_width - visible_prefix_len - wcswidth(item_title)) * " "
            colored_item = f"{selected_bg}{color_viewed}{color_bookmarked}{wrapped_item_title}{padding}{link_colored}{self.RESET}"

            print_menu_buffer.append(f"{prefix}{colored_item}{self.RESET}")
        print_menu_buffer.append("")
        return print_menu_buffer

    def map_user_input(self, prompt=None):
        input_handler = InputHandler()
        user_input = input_handler.get_input(prompt).strip()

        input_map = {
            ReturnCode.NEXT_PAGE: "N",
            ReturnCode.PREV_PAGE: "P",
            ReturnCode.LINE_UP: "U",
            ReturnCode.LINE_DOWN: "D",
        }

        if mapped_key := input_map.get(user_input):
            return mapped_key

        return user_input

    def print_user_input(self):
        try:
            prompt = f"{self.BRIGHT_BLUE}{self.BOLD}Select: {self.RESET}"
            self.user_input = self.map_user_input(prompt)
        except KeyboardInterrupt:
            OSManager.exit(0)

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

            ans: Video = self.data[self.choosed_item]
            # self.mark_viewed(ans["video_url"]) # To avoid hidden actions, should not be used internally in functions should only have display handling functions
            self._last_played = (
                self.choosed_item
            )  # save the episode just played to enter next time auto next

            self.choosed_item = self._find_next_unviewed_index(self.choosed_item + 1)
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
                self.choosed_item = self._find_next_unviewed_index(start_idx)
                self.cursor_in_page = (
                    self.choosed_item - self.index_item * self.opts.items_per_list
                )
                self.cursor_moved = False
            case "P":
                self.index_item -= 1
                self.valid_index_item()
                start_idx = self.index_item * self.opts.items_per_list
                self.choosed_item = self._find_next_unviewed_index(start_idx)
                self.cursor_in_page = (
                    self.choosed_item - self.index_item * self.opts.items_per_list
                )
                self.cursor_moved = False
            case "J":
                self.choosed_item = self._find_next_unviewed_index(self.choosed_item)
                self.valid_index_item()
                self.index_item = self.choosed_item // self.opts.items_per_list
            case "U":
                if self.cursor_in_page > 0:
                    self.cursor_in_page -= 1
                self.cursor_moved = True
                self.choosed_item = (
                    self.index_item * self.opts.items_per_list + self.cursor_in_page
                )
            case "D":
                if self.cursor_in_page < len(self.splited_data_items) - 1:
                    self.cursor_in_page += 1
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
        print_buffer = "\n".join(line for arg in args for line in arg)
        return print_buffer

    def choose_menu(self, playlists, clear_choosed_item=False):
        playlists = LegacyCompatibility.normalize_playlist(playlists)

        self.data = playlists
        self.clear_choosed_item = clear_choosed_item
        self.pagination()

        if self.clear_choosed_item or self.choosed_item is False:
            self.choosed_item = self._find_first_unviewed_index()

        self.index_item = self.choosed_item // self.opts.items_per_list

        try:
            while True:
                self.valid_index_item()

                self.splited_data_items = self.splited_data[self.index_item]
                self.len_data_items = len(self.splited_data_items)

                print_option_buffer = self.print_option()
                print_page_indicator_buffer = self.print_page_indicator()
                print_menu_buffer = self.print_menu()

                print_buffer = self.prepare_buffer(
                    print_option_buffer, print_page_indicator_buffer, print_menu_buffer
                )

                self.clscr()
                print(print_buffer)

                self.print_user_input()

                if self.advanced_options():
                    continue

                if self.standard_options():
                    continue

                if ans := self.choose_item_option():
                    return ans
        finally:
            self._init_loop_values_()
