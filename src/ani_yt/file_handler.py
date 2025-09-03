import ujson as json

# Custom lib
from .os_manager import OSManager


class InitializeOPTS:
    dirs = ["data", "mpv-config", "mpv-scripts"]


class Initialize:
    @staticmethod
    def directory():
        OSManager.initialize_directory(InitializeOPTS.dirs)


class FileHandler:
    def __init__(self):
        self.filename = "./data/playlists.json"
        self.encoding = "utf-8"

    def dump(self, video_list):
        with open(self.filename, "w", encoding=self.encoding) as f:
            json.dump(video_list, f, indent=4)

    def load(self):
        with open(self.filename, "r", encoding=self.encoding) as f:
            return json.load(f)

    def clear_cache(self):
        OSManager.delete_file(self.filename)


class FileSourceHandler:
    def __init__(self):
        self.source_filename = "./data/channel_sources.txt"
        self.encoding = "utf-8"
        self.notation = "# This is a list of channel sources used for multiple source updates.\n# Each line is the value of the -c/--channel CHANNEL argument.\n"

    def safe_load(func):
        def helper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except FileNotFoundError:
                self.placeholder()
                return []

        return helper

    def placeholder(self):
        with open(self.source_filename, "w", encoding=self.encoding) as f:
            f.write(self.notation)

    @safe_load
    def load(self):
        with open(self.source_filename, "r", encoding=self.encoding) as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]

    def save(self, sources):
        with open(self.source_filename, "w", encoding=self.encoding) as f:
            f.write(self.notation)
            for src in sources:
                f.write(f"{src}\n")

    def add_sources(self, *urls):
        sources = self.load()
        added = 0
        for url in urls:
            if url not in sources:
                sources.append(url)
                added += 1
        if added > 0:
            self.save(sources)
        return added

    def remove_sources(self, *urls):
        sources = self.load()
        removed = 0
        for url in urls:
            if url in sources:
                sources.remove(url)
                removed += 1
        if removed > 0:
            self.save(sources)
        return removed
