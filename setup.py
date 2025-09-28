from setuptools import Extension, setup
from setuptools.command.build_py import build_py as _build_py
import os
import shutil
import subprocess

SOURCE_ONLY = os.environ.get("SOURCE_ONLY") == "1"
USE_CYTHON = not SOURCE_ONLY

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False


class build_py(_build_py):
    def run(self):
        if shutil.which("go") is None or os.environ.get("GO_BUILD") == "0":
            print("Skipping Go build, 'go' not found")
        else:
            print(f"Building Go binary at {output_bin} ...")
            repo_root = os.path.abspath(os.path.dirname(__file__))
            bin_dir = os.path.join(repo_root, "bin")
            os.makedirs(bin_dir, exist_ok=True)

            go_src = os.path.join(repo_root, "src", "ani_tracker")
            output_bin = os.path.join(bin_dir, "ani-tracker")
            subprocess.check_call(["go", "build", "-o", output_bin, "."], cwd=go_src)

        super().run()

extensions = [
    Extension(
        name="ani_yt._query",
        sources=[os.path.join("src", "ani_yt", "_query" + (".pyx" if USE_CYTHON else ".c"))],
    )
]


if USE_CYTHON:
    extensions = cythonize(extensions, language_level=3)

setup(
    name="AniYT",
    ext_modules=extensions,
    package_dir={"": "src"},
)
