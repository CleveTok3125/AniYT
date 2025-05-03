import ujson as json

# Custom lib
from os_manager import OSManager


class HistoryHandler:
    def __init__(self):
        self.filename = "history.json"
        self.encoding = "utf-8"

    def is_history(self):
        return OSManager.exists(self.filename)

    def load(self):
        with open(self.filename, "r", encoding=self.encoding) as f:
            return json.load(f)

    def update(self, curr="", playlist="", videos=""):
        is_history = self.is_history()
        if is_history:
            content = self.load()
        content = {
            "current": content["current"] if is_history and not curr else curr,
            "playlist": content["playlist"]
            if is_history and not playlist
            else playlist,
            "videos": content["videos"] if is_history and not videos else videos,
        }

        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(content, f, indent=4)

    def search(self, curr_url, history):
        history = history["videos"]
        for index in range(len(history)):
            if history[index][1] == curr_url:
                return index
        return -1

    def delete_history(self):
        OSManager.delete_file(self.filename)
