import os
import sys
from datetime import datetime
from time import sleep
from typing import Dict, List

from .bookmarking_handler import BookmarkingHandler
from .data_processing import DataProcessing
from .helper import LegacyCompatibility
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
    def search():
        return str(input("Search: "))

    @staticmethod
    def clscr():
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")


class DisplayExtensionFallback:
    # Ensures the program still works even if the extension cannot be loaded

    @staticmethod
    def fallback_bookmark_handler():
        # Mock BookmarkingHandler for fallback purposes
        class MockBookmarkingHandler(BookmarkingHandler):
            def __init__(self):
                pass  # No need to reinitialize attributes, just override methods as needed

            def is_bookmarked(self, url):
                # Override the method to always return False (or any desired value for mock)
                return False

            def remove_bookmark(self, url):
                # Mock the behavior of removing a bookmark
                print(f"[Mock] Removed bookmark for: {url}")

            def update(self, data):
                # Mock the behavior of updating a bookmark
                print(f"[Mock] Updated bookmark: {data}")

        return MockBookmarkingHandler()

    @staticmethod
    def fallback_yt_dlp_opts():
        return YT_DLP_Options(quiet=True, no_warnings=True)


class DisplayExtension:
    def _inject_dependencies(
        self,
    ):  # Only used when you want to declare an instance, other values ​​like str, int, list, etc can be taken directly from extra_opts
        self.bookmarking_handler = self._get_dependencies(
            "bookmark",
            BookmarkingHandler,
            fallback_factory=DisplayExtensionFallback.fallback_bookmark_handler,
        )

        self.yt_dlp_opts = self._get_dependencies(
            "yt-dlp",
            YT_DLP_Options,
            fallback_factory=DisplayExtensionFallback.fallback_yt_dlp_opts,
        )

    def _init_extra_opts(self, extra_opts):
        self.extra_opts = extra_opts

        if not isinstance(extra_opts, dict):
            raise TypeError(
                f"The parameter passed should be a dictionary, but got {type(extra_opts)}"
            )

    def _get_dependencies_errors(self, requirement, requirement_suggestion, dependency):
        if not dependency:
            raise ValueError(
                f"Missing required dependency: '{requirement}' is not provided. Need instance of class {requirement_suggestion}"
            )
        elif not isinstance(dependency, requirement_suggestion):
            raise TypeError(
                f"Instance {dependency} is not an instance of class {requirement_suggestion}"
            )
        elif isinstance(dependency, type):
            raise TypeError(
                f"The dependency '{requirement}' should be an instance, but got a class: {dependency}"
            )
        elif dependency.__class__.__module__ == "builtins":
            raise TypeError(
                f"The dependency '{requirement}' should be an instance of a user-defined class, but got built-in type: {type(dependency)}"
            )

    def _get_dependencies(
        self, requirement: object, requirement_suggestion: type, fallback_factory=None
    ):
        dependency = self.extra_opts.get(requirement)
        strict_mode = self.extra_opts.get("strict_mode", False)
        default_warning_time = 1
        warning_time = self.extra_opts.get("warning_time", default_warning_time)

        if not isinstance(strict_mode, bool):
            strict_mode = False

        if isinstance(warning_time, str):
            warning_time = (
                int(warning_time) if warning_time.isdigit() else default_warning_time
            )
        elif not isinstance(warning_time, int):
            warning_time = default_warning_time

        if strict_mode:
            print(f"[StrictMode] Checking '{requirement}' strictly.")
            self._get_dependencies_errors(
                requirement, requirement_suggestion, dependency
            )
        else:
            try:
                self._get_dependencies_errors(
                    requirement, requirement_suggestion, dependency
                )
            except (ValueError, TypeError) as e:
                if fallback_factory:
                    print(f"{type(e).__name__}: {e}")
                    fallback = fallback_factory()

                    if not isinstance(fallback, requirement_suggestion):
                        raise TypeError(
                            f"Fallback for '{requirement}' is not valid instance of {requirement_suggestion}"
                        )

                    print(
                        f"[WARN] Using fallback for '{requirement}': {fallback.__class__.__name__}"
                    )
                    self.extra_opts[requirement] = fallback
                    dependency = fallback

                    if warning_time == -1:
                        input()
                    else:
                        sleep(warning_time)

        return dependency

    def bookmark_processing(self, user_int):
        try:
            item: Video = self.data[user_int - 1]
            if self.bookmarking_handler.is_bookmarked(item["video_url"]):
                self.bookmarking_handler.remove_bookmark(item["video_url"])
            else:
                self.bookmarking_handler.update(item)
        except ValueError:
            input("ValueError: only non-negative integers are accepted.\n")
        except IndexError:
            input("IndexError: The requested item is not listed.\n")

    def open_image_with_mpv(self, url):
        Player.start_with_mode(url=url, opts=self.extra_opts.get("mode", "auto"))

    def show_thumbnail(self, user_int):
        item: Video = self.data[user_int - 1]
        url = item["video_url"]

        thumbnail_url = YT_DLP.standalone_get_thumbnail(url, self.yt_dlp_opts.ydl_opts)
        self.open_image_with_mpv(thumbnail_url)


class DisplayMenu(Display, DisplayExtension):
    """
    DisplayMenu handles the presentation and navigation of video playlists with features like:
    - Paging through videos
    - Bookmarking
    - Showing/hiding additional options
    - Auto-selecting the next unviewed video
    - Thumbnail preview

    Key Features Overview:

    1. Initialization (__init__):
        - Sets up user options, display settings, and history map.
        - Static options (pages_opts) and dynamic options (B_toggle, O_toggle) are combined.
        - History is loaded to know which videos were already viewed.

    2. Options Handling:
        - Static options: navigation, jump to page, view thumbnail, quit.
        - Dynamic options: toggle bookmark, show/hide all options.
        - Options are stored in a dict with meaningful keys, then merged into `combined_opts`.
        - `page_opts_display` contains the formatted string for display.

    3. Auto-Select Mechanism:
        - `_find_first_unviewed_index()` finds the first video not marked as 'viewed'.
        - `_find_next_unviewed_index(start_idx)` finds the next unviewed video from a starting index.
        - During `print_menu()`, the first unviewed video on the current page is automatically set as `choosed_item`.
        - In `choose_item_option()`:
            * If the user presses Enter without typing a number, `choosed_item` is auto-selected.
            * If `_last_played` exists and matches `choosed_item`, the index increments to the next item for auto-play.
        - This ensures the menu always highlights the next video the user hasn't watched yet.
        - After selection, `_last_played` is updated so subsequent auto-selects work correctly.

    4. Pagination:
        - `pagination()` splits the playlist into pages according to `items_per_list`.
        - Keeps track of current page, total items, items per page, and last page length.
        - `index_item` tracks the current page index.
        - `len_data_items` tracks number of videos on the current page.

    5. Menu Rendering:
        - `print_option()` shows either all options (if `show_opts=True`) or just toggle hint.
        - `print_page_indicator()` shows current page / total pages and items shown.
        - `print_menu()` prints each video title with colors:
            * Gray if already viewed
            * Yellow if bookmarked
            * Appends video URL if `show_link=True`
        - The first unviewed video on the page becomes the default selected item.

    6. User Input Processing:
        - `print_user_input()` asks the user to select an item.
        - `advanced_options()` handles commands with parameters:
            * "P:<int>" → jump to page
            * "B:<int>" → toggle bookmark on a specific video
            * "I:<int>" → change number of items per page
            * "T:<int>" → view thumbnail
        - `choose_item_option()` selects a video either based on input or auto-selection logic.
        - `standard_options()` handles simple single-key commands:
            * N/P → next/previous page
            * J → jump to next unviewed video
            * U → toggle URL display
            * O → toggle full options
            * B → toggle bookmark mode
            * Q → quit

    7. Menu Loop (choose_menu):
        - Clears screen and redraws menu every iteration.
        - Updates page info and options display dynamically.
        - Continues until a valid video selection is made, which is returned as (title, URL).
        - Ensures indices are valid and resets loop variables after exit.

    8. Bookmark / Viewed Tracking:
        - Bookmarks are toggled via `bookmark_processing()`.
        - Viewed videos are tracked via `history_handler` and local `history_map`.
        - `mark_viewed(url)` updates both history file and local map.

    Overall Flow:
        __init__ → load history & set up options → choose_menu → render menu → wait for user input → handle input → auto-select next unviewed → return selected video
    """

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
        self.RESET = "\033[0m"
        self.YELLOW = "\033[33m"
        self.LIGHT_GRAY = "\033[38;5;247m"
        self.BLUE = "\033[0;34;49m"

        # Variable
        self._init_loop_values_()

        # Constant
        self.no_opts = {
            "option_toggle": ["(O) Hide all options", "(O) Show all options"],
        }
        self.pages_opts = {
            "N": "(N) Next page",
            "P": "(P) Previous page",
            "P_int": "(P:<integer>) Jump to page",
            "J": "(J) Jump to next unviewed",
            "U": "(U) Move cursor up",
            "D": "(D) Move cursor down",
            "L": "(L) Toggle link",
            "B_int": "(B:<integer>) Add/remove bookmark",
            "T_int": "(T:<integer>) View thumbnail",
            "I_int": "(I:<integer>) number of items per page",
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
        return start_idx

    def _render_dynamic_opts(self):
        self.combined_opts = self.pages_opts.copy()

        self.combined_opts["B_toggle"] = (
            f"{self.YELLOW if self.bookmark else ''}(B) Toggle bookmark{self.RESET}"
        )
        self.combined_opts["O_toggle"] = (
            self.no_opts["option_toggle"][0]
            if not self.opts.show_opts
            else self.no_opts["option_toggle"][1]
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
        if self.choosed_item >= self.len_data:
            self.choosed_item = False

        if self.index_item >= self.len_data:
            self.index_item = 0
        elif self.index_item <= -1:
            self.index_item = self.len_data - 1

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
            output = self.no_opts["option_toggle"][0]
        print(f"{output}\n")

    def print_page_indicator(self):
        showed_item = self.len_data_items + self.index_item * self.opts.items_per_list
        print(
            f"Page: {self.index_item + 1}/{self.len_data} ({showed_item}/{self.total_items})\n"
        )

    def print_menu(self):
        self.len_data_items = len(self.splited_data_items)
        first_unviewed_set = False

        unviewed_indicator = f"{self.YELLOW}❯{self.RESET}"
        cursor_in_page = f"{self.BLUE}❯{self.RESET}"

        for index, item in enumerate(self.splited_data_items):
            item_title = item["video_title"]
            item_url = item["video_url"]

            item_number = self.index_item * self.opts.items_per_list + index + 1

            color_viewed = (
                self.LIGHT_GRAY
                if self.history_map.get(item_url, "").lower() == "viewed"
                else ""
            )

            if not first_unviewed_set and color_viewed == "" and not self.cursor_moved:
                self.choosed_item = item_number - 1
                first_unviewed_set = True

            color_bookmarked = (
                self.YELLOW
                if getattr(self, "bookmark", True)
                and self.bookmarking_handler.is_bookmarked(item_url)
                else ""
            )

            link = f"\n\t{item_url}" if self.show_link else ""

            indicate_item = " "
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

            print(
                f"{self.RESET} {indicate_item} {color_viewed}{color_bookmarked}({item_number}) {item_title}{link}{self.RESET}"
            )
        print()

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
            prompt = "Select: "
            self.user_input = self.map_user_input(prompt)
        except KeyboardInterrupt:
            OSManager.exit(0)

    def advanced_options(self):
        if len(self.user_input) >= 3 and (user_int := self.user_input[2:]).isdigit():
            user_int = int(user_int)
            user_input = self.user_input[:2].upper()
            if user_input == "P:":
                self.index_item = user_int - 1
            elif user_input == "B:":
                self.bookmark_processing(user_int)
            elif user_input == "I:":
                self.opts.items_per_list = (
                    user_int
                    if user_int > 0
                    else self.total_items if user_int > self.total_items else 1
                )
                self.pagination()
            elif user_input == "T:":
                self.show_thumbnail(user_int)
            else:
                return False
            return True
        return False

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
                ):
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
            # save the episode just played to enter next time auto next
            self._last_played = self.choosed_item
            return ans["video_title"], ans["video_url"]

        except ValueError:
            input("ValueError: only options and non-negative integers are accepted.\n")
        except IndexError:
            input("IndexError: The requested item is not listed.\n")
        return

    def standard_options(self):
        user_input = self.user_input.upper()
        if user_input == "O":
            self.opts.show_opts = not self.opts.show_opts
            return True
        if user_input == "N":
            self.index_item += 1
            self.cursor_in_page = 0
            self.cursor_moved = False
            return True
        if user_input == "P":
            self.index_item -= 1
            self.cursor_in_page = 0
            self.cursor_moved = False
            return True
        if user_input == "J":
            self.choosed_item = self._find_next_unviewed_index(self.choosed_item)
            self.index_item = self.choosed_item // self.opts.items_per_list
            return True
        if user_input == "U":
            if self.cursor_in_page > 0:
                self.cursor_in_page -= 1
            self.cursor_moved = True
            self.choosed_item = (
                self.index_item * self.opts.items_per_list + self.cursor_in_page
            )
            return True
        if user_input == "D":
            if self.cursor_in_page < len(self.splited_data_items) - 1:
                self.cursor_in_page += 1
            self.cursor_moved = True
            self.choosed_item = (
                self.index_item * self.opts.items_per_list + self.cursor_in_page
            )
            return True
        if user_input == "L":
            self.show_link = not self.show_link
            return True
        if user_input == "B":
            self.bookmark = not self.bookmark
            self._render_dynamic_opts()
            return True
        if user_input == "Q":
            OSManager.exit(0)
        return False

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
                self.clscr()

                self.valid_index_item()

                self.splited_data_items = self.splited_data[self.index_item]
                self.len_data_items = len(self.splited_data_items)

                self.print_option()
                self.print_page_indicator()
                self.print_menu()

                self.print_user_input()

                if self.advanced_options():
                    continue

                if self.standard_options():
                    continue

                if ans := self.choose_item_option():
                    return ans
        finally:
            self._init_loop_values_()
