import os
import sys
from time import sleep

from .bookmarking_handler import BookmarkingHandler
from .data_processing import DataProcessing
from .os_manager import OSManager
from .player import Player
from .yt_dlp_handler import YT_DLP, YT_DLP_Options


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
            if self.bookmarking_handler.is_bookmarked(
                (item := self.data[user_int - 1])[1]
            ):
                self.bookmarking_handler.remove_bookmark(item[1])
            else:
                self.bookmarking_handler.update(item)
        except ValueError:
            input("ValueError: only non-negative integers are accepted.\n")
        except IndexError:
            input("IndexError: The requested item is not listed.\n")

    def open_image_with_mpv(self, url):
        Player.start_with_mode(url=url, opts=self.extra_opts.get("mode", "auto"))

    def show_thumbnail(self, user_int):
        url = self.data[user_int - 1][1]

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
        self.data = []
        self.splited_data = []
        self.len_data = 0
        self.len_last_item = 0
        self.total_items = 0
        self.len_data_items = 0
        self.clear_choosed_item = False

        # Variable
        # These are variables that are manually cleared for caching purposes. Remember to clear these variables when running functions in the class multiple times.
        self.choosed_item = False

        # Constant
        self.no_opts = ["(O) Hide all options", "(O) Show all options"]
        self.pages_opts = [
            "(N) Next page",
            "(P) Previous page",
            "(P:<integer>) Jump to page",
        ]
        self.page_opts = [
            self.no_opts[0],
            "(U) Toggle link",
            "(B) Toggle bookmark",
            "(B:<integer>) Add/remove bookmark",
            "(T:<integer>) View thumbnail",
            "(I:<integer>) number of items per page",
            "(Q) Quit",
        ]
        self.pages_opts = "\n".join(self.pages_opts)
        self.page_opts = "\n".join(self.page_opts)

        # Constant
        self.RESET = "\033[0m"
        self.YELLOW = "\033[33m"
        self.LIGHT_GRAY = "\033[38;5;247m"

        # Variable
        self._init_loop_values_()

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
        self.show_link = self.opts.show_link
        self.bookmark = self.opts.bookmark

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
            if self.len_data > 1:
                output = f"{self.pages_opts}\n{self.page_opts}"
            else:
                output = self.page_opts
        else:
            output = self.no_opts[1]
        print(f"{output}\n")

    def print_page_indicator(self):
        showed_item = self.len_data_items + self.index_item * self.opts.items_per_list
        print(
            f"Page: {self.index_item + 1}/{self.len_data} ({showed_item}/{self.total_items})\n"
        )

    def print_menu(self):
        skip_choose_item = False

        for index in range(self.len_data_items):
            item = self.splited_data_items[index]
            item_title = item[0]
            item_url = item[1]

            item_number = self.index_item * self.opts.items_per_list + index + 1

            color_viewed = ""
            if len(item) >= 3 and item[2].lower() == "viewed":
                color_viewed = self.LIGHT_GRAY
            elif not skip_choose_item:
                skip_choose_item = True
                self.choosed_item = item_number - 1

            color_bookmarked = (
                self.YELLOW
                if self.bookmark and self.bookmarking_handler.is_bookmarked(item_url)
                else ""
            )

            link = f"\n\t{item_url}" if self.show_link else ""

            print(
                f"{self.RESET}{color_viewed}{color_bookmarked}({item_number}) {item_title}{link}{self.RESET}"
            )
        print()

    def print_user_input(self):
        try:
            self.user_input = input("Select: ").strip()
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

    def choose_item_option(self):
        try:
            if self.clear_choosed_item:
                self.choosed_item = False

            if self.user_input == "":
                self.choosed_item += 1
                self.user_input = str(self.choosed_item)
                return self.choose_item_option()

            if not self.user_input.isdigit():
                raise ValueError()

            self.choosed_item = int(self.user_input)
            ans = self.data[self.choosed_item - 1]
            return ans[0], ans[1]

        except ValueError:
            input("ValueError: only options and non-negative integers are accepted.\n")
        except IndexError:
            input("IndexError: The requested item is not listed.\n")
        return

    def standard_options(self):
        user_input = self.user_input.upper()
        if user_input == "O":
            self.opts.show_opts = not self.opts.show_opts
        elif user_input == "N":
            self.index_item += 1
        elif user_input == "P":
            self.index_item -= 1
        elif user_input == "U":
            self.show_link = not self.show_link
        elif user_input == "B":
            self.bookmark = not self.bookmark
        elif user_input == "Q":
            OSManager.exit(0)
        else:
            return self.choose_item_option()
        return

    def choose_menu(self, data, clear_choosed_item=False):
        """
        How auto-select (guessing user choices) feature works
        1. __init__()
        Initialize self.choosed_item
        2. print_menu()
        Assign a default value to self.choosed_item
        This value is the index of the latest episode the user has watched
        If not, self.choosed_item retains its initial value
        3. choose_item_option()
        If the user specifies a specific number (for self.user_input), it overwrites the default value of self.choosed_item
        If not, self.choosed_item is incremented by 1 (the index of the next episode) and overwrites self.user_input
        When the value of self.choosed_item is the initial value, it is automatically processed as index 0 and returns a value of 1 (the first episode in the list)
        4. valid_index_item()
        In case self.choosed_item exceeds the valid limit, it will be set to its initial value.
        """

        self.data = data
        self.clear_choosed_item = clear_choosed_item
        self.pagination()

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

                if ans := self.standard_options():
                    return ans
                else:
                    continue
        finally:
            self._init_loop_values_()
