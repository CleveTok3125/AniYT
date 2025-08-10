import ujson as json

# Custom lib
from .os_manager import OSManager


class BookmarkingHandler:
    def __init__(self):
        self.filename = "bookmark.json"
        self.encoding = "utf-8"

    def is_bookmarking(self):
        return OSManager.exists(self.filename)

    def load(self):
        with open(self.filename, "r", encoding=self.encoding) as f:
            return json.load(f)

    def update(self, data):
        if self.is_bookmarking():
            content = self.load()
        else:
            content = {}

        content[data[0]] = data[1]

        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(content, f, indent=4)

    def is_bookmarked(self, url):
        if not self.is_bookmarking():
            return False
        content = self.load()
        return url in content.values()

    def remove_bookmark(self, url):
        if not self.is_bookmarking():
            return
        content = self.load()
        for key, value in list(content.items()):
            if value == url:
                del content[key]
                break
        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(content, f, indent=4)

    def delete_bookmark(self):
        OSManager.delete_file(self.filename)
