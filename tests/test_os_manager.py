import os

from ani_yt.os_manager import OSManager


class TestOSManager:
    def test_exists(self):
        assert OSManager.exists(os.getcwd())

    def test_not_exists(self):
        assert not OSManager.exists("/nonexistent_path_xyz")

    def test_isdir(self):
        assert OSManager.isdir(os.getcwd())

    def test_not_isdir(self):
        f = "temp_test_file.txt"
        with open(f, "w") as fh:
            fh.write("test")
        assert not OSManager.isdir(f)
        os.remove(f)

    def test_delete_file(self):
        f = "temp_test_file.txt"
        with open(f, "w") as fh:
            fh.write("test")
        assert os.path.exists(f)
        OSManager.delete_file(f)
        assert not os.path.exists(f)

    def test_delete_nonexistent(self):
        OSManager.delete_file("/nonexistent_xyz")

    def test_initialize_directory(self):
        OSManager.initialize_directory(["test_dir_a", "test_dir_b"])
        assert os.path.isdir("test_dir_a")
        assert os.path.isdir("test_dir_b")
        os.rmdir("test_dir_a")
        os.rmdir("test_dir_b")

    def test_temporary_session(self):
        orig = os.getcwd()
        path = OSManager.temporary_session()
        assert os.path.isdir(path)
        assert os.getcwd() == path
        os.chdir(orig)

    def test_working_directory_valid(self):
        d, abs_path = OSManager.working_directory(os.getcwd())
        assert d is not None
        assert abs_path is not None

    def test_working_directory_invalid(self):
        d, abs_path = OSManager.working_directory("/nonexistent_path_xyz")
        assert d is None
        assert abs_path is None

    def test_ensure_parent_dir_same(self):
        orig = os.getcwd()
        target = OSManager.ensure_parent_dir(os.path.basename(orig))
        assert target == orig
