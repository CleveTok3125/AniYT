import os
import sys
from typing import List

from ._internal._display_color import DisplayColor
from ._internal._display_extension import DisplayExtension
from ._internal._display_rendering import DisplayRendering
from .common import Typing
from .data_processing import DataProcessing
from .exceptions import PauseableException
from .helper import IOHelper, LegacyCompatibility
from .os_manager import OSManager


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


class DisplayMenu(Display, DisplayRendering, DisplayExtension):
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
            "option_toggle": {
                "hide": {
                    "key": "(O)",
                    "desc": f"{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}Hide all options{DisplayColor.RESET}",
                },
                "show": {
                    "key": "(O)",
                    "desc": f"{DisplayColor.BRIGHT_BLUE}{DisplayColor.BOLD}Show all options{DisplayColor.RESET}",
                },
            }
        }
        self.pages_opts = {
            "N": {"key": "(N/→)", "desc": "Next page"},
            "P": {"key": "(P/←)", "desc": "Previous page"},
            "P_int": {"key": "(P:<id>)", "desc": "Jump to page"},
            "J": {"key": "(J)", "desc": "Jump to next unviewed"},
            "U": {"key": "(U/↑)", "desc": "Move cursor up"},
            "D": {"key": "(D/↓)", "desc": "Move cursor down"},
            "B_int": {
                "key": "(B:[<id>]",
                "desc": "Add/remove bookmark",
                "is_multiline_start": True,
            },
            "B_int_ext1": {
                "key": "[:<cat>{bookmark,completed}]",
                "desc": "",
                "is_multiline_ext": True,
            },
            "B_int_ext2": {
                "key": "[:<action>{new}])",
                "desc": "",
                "is_multiline_ext": True,
            },
            "V_int": {"key": "(V:<id>)", "desc": "Toggle viewed status"},
            "T_int": {"key": "(T:<id>)", "desc": "View thumbnail"},
            "I_int": {"key": "(I:<id>)", "desc": "Number of items per page"},
            "R": {"key": "(R)", "desc": "Re-render the interface"},
            "Q": {"key": "(Q)", "desc": "Quit"},
        }

        # Dynamic
        self.render_dynamic_opts()

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

    def _get_page_start_index(self) -> int:
        """Calculates the starting index of the items on the current page."""
        return self.index_item * self.opts.items_per_list

    def valid_index_item(self):
        if self.index_item >= self.len_data:
            self.index_item = 0
        elif self.index_item <= -1:
            self.index_item = self.len_data - 1

    def sync_cursor_with_item(self):
        if not self.splited_data:
            return

        self.cursor_in_page = self.choosed_item - self._get_page_start_index()

        self.cursor_in_page = max(
            0, min(self.cursor_in_page, len(self.splited_data[self.index_item]) - 1)
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

        # Make sure the cursor doesn't stray when changing items_per_list
        if self.choosed_item is not False:
            self.sync_cursor_with_item()

    def toggle_viewed_processing(self, item_number):
        """Gets item number, finds the URL, and calls the toggle handler."""
        index = item_number - 1
        if 0 <= index < len(self.data):
            video_url = self.data[index]["video_url"]
            self.toggle_viewed_status(video_url)
        else:
            PauseableException("IndexError: Invalid item number.", delay=-1)

    def advanced_options(self):
        # K:integer:option

        user_input_parts = self.user_input.split(":")
        len_user_input_parts = len(user_input_parts)

        user_input_upper = (f"{user_input_parts[0]}:").upper()
        has_item_specified = (
            len_user_input_parts >= 2 and (user_int := user_input_parts[1]).isdigit()
        )
        is_cursor_option = len_user_input_parts >= 2 and user_input_parts[1] == ""
        is_user_option = len_user_input_parts >= 3 and user_input_parts[2] != ""
        is_user_action = len_user_input_parts >= 4 and user_input_parts[3] != ""

        if is_user_option:
            user_option = user_input_parts[2]

        if is_user_action:
            user_action = user_input_parts[3].lower()

        if has_item_specified:
            user_int = int(user_int)

        if is_cursor_option and not has_item_specified:
            if self.cursor_moved:
                user_int = self._get_page_start_index() + self.cursor_in_page + 1
            else:
                user_int = self.choosed_item + 1

        if not any([is_cursor_option, has_item_specified]):
            return False

        match (user_input_upper, is_cursor_option):
            case ("B:", _):
                category = user_option if is_user_option else "bookmark"
                action = True if is_user_action and user_action == "new" else False
                self.mark_bookmark(user_int, category=category, create_new=action)
            case ("V:", _):
                self.toggle_viewed_processing(user_int)
            case ("T:", _):
                self.show_thumbnail(user_int)
            case ("P:", False):
                self.index_item = user_int - 1
                self.valid_index_item()

                # Automatically jump to and sync cursor when jumping to specific page
                self.choosed_item = self.find_next_unviewed_index(
                    self._get_page_start_index()
                )
                self.sync_cursor_with_item()
            case ("I:", False):
                self.opts.items_per_list = (
                    user_int
                    if user_int > 0
                    else self.total_items if user_int > self.total_items else 1
                )
                self.pagination()

                # Sync fix
                self.valid_index_item()
                self.sync_cursor_with_item()
            case _:
                return False

        return True

    def _handle_enter_input(self):
        # If enter is pressed when the cursor is already on a specific item
        if self.cursor_moved:
            self.choosed_item = self._get_page_start_index() + self.cursor_in_page
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
            self.sync_cursor_with_item()
            self.cursor_moved = False

            return ans["video_title"], ans["video_url"]

        except ValueError:
            PauseableException(
                "ValueError: only options and non-negative integers are accepted.",
                delay=-1,
            )
        except IndexError:
            PauseableException(
                "IndexError: The requested item is not listed.", delay=-1
            )
        return

    def standard_options(self):
        user_input = self.user_input.upper()
        handled = True

        match user_input:
            case "O":
                self.opts.show_opts = not self.opts.show_opts
                self.render_dynamic_opts()
            case "N":
                self.index_item += 1
                self.valid_index_item()
                start_idx = self._get_page_start_index()
                self.choosed_item = self.find_next_unviewed_index(start_idx)
                self.sync_cursor_with_item()
                self.cursor_moved = False
            case "P":
                self.index_item -= 1
                self.valid_index_item()
                start_idx = self._get_page_start_index()
                self.choosed_item = self.find_next_unviewed_index(start_idx)
                self.sync_cursor_with_item()
                self.cursor_moved = False
            case "J":
                self.choosed_item = self.find_next_unviewed_index(self.choosed_item)
                self.valid_index_item()
                self.index_item = self.choosed_item // self.opts.items_per_list
                self.sync_cursor_with_item()
            case "U":
                if self.cursor_in_page > 0:
                    self.cursor_in_page -= 1
                else:
                    self.cursor_in_page = len(self.splited_data_items) - 1
                self.cursor_moved = True
                self.choosed_item = self._get_page_start_index() + self.cursor_in_page
            case "D":
                if self.cursor_in_page < len(self.splited_data_items) - 1:
                    self.cursor_in_page += 1
                else:
                    self.cursor_in_page = 0
                self.cursor_moved = True
                self.choosed_item = self._get_page_start_index() + self.cursor_in_page
            case "L":
                self.show_link = not self.show_link
                self.render_dynamic_opts()
            case "B":
                self.bookmark = not self.bookmark
                self.render_dynamic_opts()
            case "R":
                self.render_dynamic_opts()
            case "Q":
                OSManager.exit(0)
            case _:
                handled = False

        return handled

    def choose_menu(self, playlists, clear_choosed_item=False):
        playlists = LegacyCompatibility.normalize_playlist(playlists)

        self.data = playlists
        self.clear_choosed_item = clear_choosed_item
        self.pagination()

        if self.clear_choosed_item or self.choosed_item is False:
            self.choosed_item = self.find_first_unviewed_index()

        self.index_item = self.choosed_item // self.opts.items_per_list
        self.sync_cursor_with_item()

        try:
            while True:
                self.valid_index_item()

                self.splited_data_items = self.splited_data[self.index_item]
                self.len_data_items = len(self.splited_data_items)

                print_buffer = self.get_print_buffer()

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
