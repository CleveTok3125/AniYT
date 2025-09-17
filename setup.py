from setuptools import Extension, setup
import os

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

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
)
