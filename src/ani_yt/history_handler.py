import ujson as json

# Custom lib
from .os_manager import OSManager
from .exceptions import InvalidHistoryFile


class HistoryHandler:
    def __init__(self):
        self.filename = "history.json"
        self.encoding = "utf-8"
        self.required_keys = {"current", "playlist", "videos"}

    def safe_history_load(func):
        def helper(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)


                if not isinstance(result, dict):
                    raise InvalidHistoryFile(self.filename)
                if not self.required_keys.issubset(result.keys()):
                    raise InvalidHistoryFile(self.filename)
                return result
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                raise InvalidHistoryFile(self.filename)

        return helper

    def is_history(self):
        return OSManager.exists(self.filename)

    @safe_history_load
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

    @safe_history_load
    def search(self, curr_url, history):
        history = history["videos"]
        for index in range(len(history)):
            if history[index][1] == curr_url:
                return index
        return -1

    def delete_history(self):
        OSManager.delete_file(self.filename)
