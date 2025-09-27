from setuptools import Extension, setup
import os
from setuptools.command.build_py import build_py as _build_py
import subprocess


try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

class build_py(_build_py):
    def run(self):
        repo_root = os.path.abspath(os.path.dirname(__file__))
        bin_dir = os.path.join(repo_root, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        go_src = os.path.join(repo_root, "src", "ani_tracker")
        output_bin = os.path.join(bin_dir, "ani-tracker")

        print(f"Building Go binary at {output_bin} ...")
        subprocess.check_call(["go", "build", "-o", output_bin, "."], cwd=go_src)

        super().run()

extensions = [
    Extension(
        name="ani_yt._query",
        sources=[os.path.join("src", "ani_yt", "_query" + ".pyx" if USE_CYTHON else ".c")],
    )
]


if USE_CYTHON:
    extensions = cythonize(extensions, language_level=3)

setup(
    name="AniYT",
    ext_modules=extensions,
    package_dir={"": "src"},
    cmdclass={"build_py": build_py},
)
