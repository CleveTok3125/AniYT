import os

from ani_yt.file_handler import FileHandler, FileSourceHandler


class TestFileHandler:
    def test_dump_and_load(self):
        fh = FileHandler()
        data = [["Title1", "https://youtube.com/1"], ["Title2", "https://youtube.com/2"]]
        fh.dump(data)
        loaded = fh.load()
        assert loaded == data

    def test_load_empty_file(self):
        fh = FileHandler()
        os.makedirs("data", exist_ok=True)
        with open(fh.filename, "w") as f:
            f.write("[]")
        assert fh.load() == []

    def test_clear_cache(self):
        fh = FileHandler()
        fh.dump([["T", "https://youtube.com/t"]])
        assert os.path.exists(fh.filename)
        fh.clear_cache()
        assert not os.path.exists(fh.filename)


class TestFileSourceHandler:
    def test_placeholder_and_load(self):
        fsh = FileSourceHandler()
        fsh.placeholder()
        loaded = fsh.load()
        assert loaded == []

    def test_add_and_load_sources(self):
        fsh = FileSourceHandler()
        added = fsh.add_sources("https://youtube.com/@channel1", "https://youtube.com/@channel2")
        assert added == 2
        loaded = fsh.load()
        assert len(loaded) == 2

    def test_add_duplicate(self):
        fsh = FileSourceHandler()
        fsh.add_sources("https://youtube.com/@ch")
        added = fsh.add_sources("https://youtube.com/@ch")
        assert added == 0

    def test_remove_sources(self):
        fsh = FileSourceHandler()
        fsh.add_sources("https://youtube.com/@ch1", "https://youtube.com/@ch2")
        removed = fsh.remove_sources("https://youtube.com/@ch1")
        assert removed == 1
        loaded = fsh.load()
        assert len(loaded) == 1

    def test_save(self):
        fsh = FileSourceHandler()
        fsh.save(["src1", "src2"])
        loaded = fsh.load()
        assert loaded == ["src1", "src2"]
