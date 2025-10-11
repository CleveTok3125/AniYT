import functools

import ujson as json

from .exceptions import InvalidBookmarkFile
from .os_manager import OSManager


class BookmarkingHandler:
    def __init__(self):
        self.filename = "./data/bookmark.json"
        self.encoding = "utf-8"
        self.required_categories = ["bookmark", "completed"]

    def _save_full_data(self, data):
        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def validate_structure(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            data = func(self, *args, **kwargs)
            required_categories = getattr(self, "required_categories", [])

            if not isinstance(data, dict):
                raise InvalidBookmarkFile(
                    "Data structure must be a dictionary", self.filename
                )

            for category in required_categories:
                if category not in data:
                    raise InvalidBookmarkFile(
                        f"Missing required category '{category}'", self.filename
                    )

                if not isinstance(data[category], dict):
                    raise InvalidBookmarkFile(
                        f"Category '{category}' must be a dictionary", self.filename
                    )

            return data

        return wrapper

    @validate_structure
    def load_full_data(self):
        if not OSManager.exists(self.filename):
            return {}
        try:
            with open(self.filename, "r", encoding=self.encoding) as f:
                content = f.read()
                return json.loads(content) if content else {}
        except (json.JSONDecodeError, IOError):
            return {}

    def get_category(self, category):
        full_data = self.load_full_data()
        return full_data.get(category, {})

    def update_item(self, data, category):
        full_data = self.load_full_data()

        if category not in full_data:
            full_data[category] = {}

        bookmarks = full_data[category]

        if isinstance(data, dict):
            key, value = data.get("video_title"), data.get("video_url")
        else:
            key, value = data[0], data[1]

        if key is None or value is None:
            raise ValueError("Data must contain title and url")

        bookmarks[key] = value
        self._save_full_data(full_data)

    def is_item_exist(self, url, category):
        items = self.get_category(category)
        return url in items.values()

    def remove_item(self, url, category):
        full_data = self.load_full_data()

        if category not in full_data:
            return

        items = full_data[category]

        key_to_delete = None
        for key, value in items.items():
            if value == url:
                key_to_delete = key
                break

        if key_to_delete:
            del items[key_to_delete]
            self._save_full_data(full_data)

    def delete_file(self):
        OSManager.delete_file(self.filename)
