from setuptools import Extension, setup
from setuptools.command.build_py import build_py as _build_py
import os
import shutil
import subprocess

SOURCE_ONLY = os.environ.get("SOURCE_ONLY") == "1"
USE_CYTHON = not SOURCE_ONLY

if USE_CYTHON:
    try:
        from Cython.Build import cythonize
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
        if shutil.which("go") is None:
            print("Skipping Go build, 'go' not found")
        else:
            subprocess.check_call(["go", "build", "-o", output_bin, "."], cwd=go_src)

        super().run()

ext_modules = []
ext = Extension(
    name="ani_yt._query",
    sources=["src/ani_yt/_query.pyx" if USE_CYTHON else "src/ani_yt/_query.c"]
)
if not SOURCE_ONLY:
    if USE_CYTHON:
        ext_modules = cythonize([ext], language_level=3)
    else:
        ext_modules = [ext]

setup(
    name="AniYT",
    ext_modules=ext_modules,
    package_dir={"": "src"},
    cmdclass={"build_py": build_py},
    setup_requires=["Cython"],
    zip_safe=False,
)
