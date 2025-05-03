import ujson as json

# Custom lib
from os_manager import OSManager


class FileHandler:
    def __init__(self):
        self.filename = "playlists.json"
        self.encoding = "utf-8"

    def dump(self, video_list):
        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(video_list, f, indent=4)

    def load(self):
        with open(self.filename, "r", encoding=self.encoding) as f:
            return json.load(f)

    def clear_cache(self):
        OSManager.delete_file(self.filename)
