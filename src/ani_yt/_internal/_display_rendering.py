import shutil

from wcwidth import wcswidth

from ._display_color import DisplayColor


class DisplayRendering:
    def _generate_color_palette(self) -> str:
        max_len = max(len(desc) for desc in DisplayColor.COLOR_MAP.values()) + 2

        lines = ["( ) Color Palette"]
        for color, description in DisplayColor.COLOR_MAP.items():
            formatted_desc = f"{description}:".ljust(max_len)
            lines.append(
                f"    {formatted_desc}{color}{DisplayColor.BLOCK}{DisplayColor.RESET}"
            )
        return "\n".join(lines)

    def render_dynamic_opts(self):
        self.combined_opts = self.pages_opts.copy()

        self.combined_opts["B_toggle"] = {
            "key": "(B)",
            "desc": "Toggle bookmark",
            "is_active": self.bookmark,
            "active_color": DisplayColor.YELLOW,
        }
        self.combined_opts["L"] = {
            "key": "(L)",
            "desc": "Toggle link",
            "is_active": self.show_link,
            "active_color": DisplayColor.LINK_COLOR,
        }
        self.combined_opts["O_toggle"] = (
            self.no_opts["option_toggle"]["show"]
            if not self.opts.show_opts
            else self.no_opts["option_toggle"]["hide"]
        )
        self.combined_opts["palette"] = self._generate_color_palette()

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
            "B_int_ext1",
            "B_int_ext2",
            "V_int",
            "T_int",
            "I_int",
            "R",
            "Q",
            "palette",
        ]

        term_width = shutil.get_terminal_size().columns

        max_key_len = max(
            wcswidth(opt["key"])
            for opt in self.combined_opts.values()
            if isinstance(opt, dict) and not opt.get("is_multiline_ext")
        )

        output_lines = []
        line_idx = 0
        for k in key_order:
            if k in self.combined_opts:
                opt = self.combined_opts[k]

                # Ignore non-dictionary items (like palette)
                if not isinstance(opt, dict):
                    output_lines.append(str(opt))
                    continue

                # Defines alternating background colors
                bg_color = (
                    DisplayColor.ALT_BG_1
                    if line_idx % 2 == 0
                    else DisplayColor.ALT_BG_2
                )

                key = opt.get("key", "")
                desc = opt.get("desc", "")

                # Define foreground color
                fg_color = ""
                if opt.get("is_active"):
                    fg_color = opt.get("active_color", DisplayColor.YELLOW)

                # Handle extended key lines (indented, same background color as main line)
                if opt.get("is_multiline_ext"):
                    prev_bg_color = (
                        DisplayColor.ALT_BG_1
                        if (line_idx - 1) % 2 == 0
                        else DisplayColor.ALT_BG_2
                    )
                    line_content = f"{DisplayColor.CONTINUATION_SYMBOL}{key}".ljust(
                        term_width
                    )
                    output_lines.append(
                        f"{prev_bg_color}{fg_color}{line_content}{DisplayColor.RESET}"
                    )
                    continue  # Do not increment line_idx for sub-lines

                left_part = key.ljust(max_key_len)
                full_line = f"{left_part} : {desc}"

                full_line = full_line.ljust(term_width)

                output_lines.append(
                    f"{bg_color}{fg_color}{full_line}{DisplayColor.RESET}"
                )
                line_idx += 1

        self.page_opts_display = "\n".join(output_lines)

    def print_option(self):
        if self.opts.show_opts:
            output = self.page_opts_display
        else:
            opt_to_show = self.no_opts["option_toggle"]["show"]
            fg_color = opt_to_show["active_color"] if opt_to_show["is_active"] else ""
            output = f"{fg_color}{opt_to_show['key']} {opt_to_show['desc']}{DisplayColor.RESET}"

        print_option_buffer = [output, ""]
        return print_option_buffer

    def print_page_indicator(self):
        showed_item = self.len_data_items + self._get_page_start_index()
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

            item_number = self._get_page_start_index() + index + 1

            color_viewed = (
                DisplayColor.LIGHT_GRAY
                if self.history_map.get(item_url, "").lower() == "viewed"
                else ""
            )

            color_bookmarked = ""
            if getattr(self, "bookmark", True):
                if self.is_item_bookmarked(item_url, "bookmark"):
                    color_bookmarked = DisplayColor.YELLOW
                elif self.is_item_bookmarked(item_url, "completed"):
                    color_bookmarked = DisplayColor.GREEN

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
            self._get_page_start_index() + self.cursor_in_page + 1
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

    def get_print_buffer(self):
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
        return print_buffer
